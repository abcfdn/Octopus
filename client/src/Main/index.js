import React, { Component } from 'react';
import { Switch, Route, BrowserRouter as Router } from 'react-router-dom'
import { Security, ImplicitCallback, SecureRoute } from '@okta/okta-react';

import Login from '../Login'
import Home from '../Home'
import Session from '../Session'

class Main extends Component {
   render() {
        return (
               <Router>
                 <Security
                   issuer={'https://dev-319775.okta.com'}
                   client_id={'0oacfy8o8fzM4RgSY356'}
                   redirect_uri={'http://206.189.161.176:8080/implicit/callback'}
                   scope={['openid', 'profile', 'email']}>

                   <Switch>
                     <Route exact path="/" component={Login} />
                     <Route path="/implicit/callback" component={ImplicitCallback} />
                     <SecureRoute path="/home" component={Home} />
                     <SecureRoute path="/session/:session_id" component={Session} />
                   </Switch>
                 </Security>
               </Router>
             );
      }
}

export default Main;