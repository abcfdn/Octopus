import axios from 'axios';

const BASE_URI = 'http://206.189.161.176:4433';

const client = axios.create({
   baseURL: BASE_URI,
   json: true
});

class APIClient {
  constructor(accessToken) {
    this.accessToken = accessToken;
  }

  getSessions() {
    return this.perform('get', '/sessions');
  }

  getSession(session_id) {
    return this.perform('get', '/session/' + session_id);
  }

  getPresenter(username) {
    return this.perform(
      'get', '/presenter/' + encodeURIComponent(username));
  }

  refresh() {
    return this.perform('post', '/refresh');
  }

  async perform(method, resource, data) {
    return client({
      method,
      url: resource,
      data,
      headers: {Authorization: `Bearer ${this.accessToken}`}
    }).then(resp => {
      return resp.data ? resp.data : [];
    })
  }
}

export default APIClient;