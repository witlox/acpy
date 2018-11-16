#!/usr/bin/env python
# -*- coding: utf-8 -*-#
#
#
# Copyright (C) 2018 University of Zurich. All rights reserved.
#
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import logging

import pyotp
from connexion import NoContent
from flask import session
from sqlalchemy.exc import SQLAlchemyError

from app import AccountRestService
from db.group import GroupUser
from db.handler import db_session
from db.user import User


logger = logging.getLogger('api.account')
auth = AccountRestService.auth


@auth.login_required
def find_groups(admin=False):
    u = db_session.query(User)
    user = u.filter(User.dom_name == session['username']).one_or_none()
    if not user:
        logger.warning("user {0} not found".format(session['username']))
        return "user doesn't exist", 404
    ua = db_session.query(GroupUser)
    ug = ua.filter(GroupUser.user == user)
    if admin:
        return [g.group.dump() for g in ug if g.admin], 200
    else:
        return [g.group.dump() for g in ug], 200


@auth.login_required
def get_user():
    u = db_session.query(User)
    user = u.filter(User.dom_name == session['username']).one_or_none()
    if not user:
        return NoContent, 404
    user.seed = pyotp.totp.TOTP().provisioning_uri(user.dom_name, issuer_name='Accounting Portal')
    return user.dump(), 200


@auth.login_required
def add_user(user):
    if 'admin' not in session:
        return NoContent, 401
    user['seed'] = pyotp.random_base32()
    u = User(**user)
    try:
        db_session.add(u)
        db_session.commit()
        return NoContent, 201
    except SQLAlchemyError:
        logger.exception("error while creating account")
        return NoContent, 500
