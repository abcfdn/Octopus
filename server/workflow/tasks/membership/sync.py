# -*- encoding: UTF-8 -*-

import os
import sys

import logging
import json
import csv

import server.platforms.utils.util as util
from server.platforms.google.sheet import GoogleSheet
from server.platforms.google.photo import GooglePhoto
from server.platforms.imgur import Imgur
from server.db.mongo import MongoConnection, MemberStore
from server.workflow.base import Task

from google.oauth2 import service_account
from .card import MembershipCard

from server.workflow.constants import MEMBERSHIP_APP

FORMAT = '%(asctime)s %(levelname)s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('member_sync')
logger.setLevel(logging.INFO)


class MemberSync(Task):
    NUM_OF_ROWS_TO_READ = 1000
    FIELDS_TO_COMPARE = ['session_name', 'presenter_name']

    def __init__(self, google_creds, imgur_creds, mongo_config):
        super().__init__(google_creds)
        self.sheet_service = GoogleSheet(google_creds)
        self.card_generator = MembershipCard(google_creds)
        self.imgur_service = Imgur(imgur_creds)
        self.photo_service = GooglePhoto(google_creds)
        self.member_store = MemberStore(MongoConnection(mongo_config))

    def app_name(self):
        return MEMBERSHIP_APP

    def merge(self, existing, new):
        member = {}
        keys = list(set().union(existing.keys(), new.keys()))
        for key in keys:
            old_value = existing.get(key, "")
            new_value = new.get(key, "")
            if len(str(old_value)) > len(str(new_value)):
                member[key] = old_value
            else:
                member[key] = new_value
        return member

    def dedupe(self, members):
        deduped_members = {}
        for member in members:
            member = self.preprocess(member)
            existing_member = deduped_members.get(member['email'], {})
            deduped_members[member['email']] = self.merge(
                existing_member, member)
        return deduped_members

    def preprocess(self, member):
        member['started_at'] = util.to_epoch_time(member['timestamp'])
        key = 'do_you_want_be_a_volunteer_for_future_abc_events_?'
        volunteer = member.get(key, 'No')
        member['volunteer_candidate'] = volunteer.lower().startswith('yes')
        member['your_full_name'] = util.canonicalize_name(member['your_full_name'])
        return self.transform_one(member)

    def sync(self):
        self.load_members()
        to_insert = []
        for member in self.members.values():
            existing_member = self.member_store.find({'email': member['email']})
            if not existing_member:
                to_insert.append(member)
        logger.info("Will insert {} among {} members".format(len(to_insert), len(self.members)))
        for member in to_insert:
            logger.info('Inserting {}'.format(member))
            self.member_store.create(member)
        self.add_membership_card()

    def add_membership_card(self):
        for member in self.members.values():
            email = member['email']
            res = self.member_store.find({
                    "email": email, "member_card":{"$exists": True}})
            if not res:
                local_path = self.card_generator.process(member)
                card = self.imgur_service.upload_photo(email, local_path)
                logger.info("Adding membership card for {} with {}".format(email, card))
                self.member_store.update(
                    {'email': email}, {'$set': {'member_card': card}})

    def load_members(self):
        self.members = []
        for source in self.config['data']['member']['remote']:
            logger.info("Reading from google file {}".format(source))
            self.members += self.load_members_from_sheet(source)
        logger.info("{} members loaded".format(len(self.members)))
        self.members = self.dedupe(self.members)
        logger.info("{} members after dedupe".format(len(self.members)))

    def load_members_from_sheet(self, source):
        return self.sheet_service.read_as_map(source, 'Form Responses 1',
            (2, self.NUM_OF_ROWS_TO_READ + 1))

    def transform_one(self, doc):
        return {
            dst: doc[src].strip() if type(doc[src]) is str else doc[src]
            for src, dst in self.config['fields']['member'].items()
            if (src in doc and doc[src])
        }
