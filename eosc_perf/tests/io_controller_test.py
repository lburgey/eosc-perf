"""This module contains unit tests for the IOController class"""
from time import time
import unittest
import json
from flask import Flask, session
from eosc_perf.model.database import configure_database
from eosc_perf.model.facade import DatabaseFacade
from eosc_perf.controller.authenticator import configure_authenticator
from eosc_perf.controller.io_controller import controller
from eosc_perf.controller.authenticator import AuthenticateError
from eosc_perf.configuration import configuration
from eosc_perf.model.data_types import Report

USER = {'exp': time() + 3600,
        'sub': 'id',
        'info': {'email': 'email@kit.edu',
                 'name': 'John Doe'}}


class IOControllerTest(unittest.TestCase):

    def setUp(self):
        """Called before each test."""
        # set up flask app necessary for flask_sqlalchemy
        self.app = Flask("Test")
        self.app.config['DEBUG'] = True
        self.app.app_context().push()
        self.app.secret_key = '!secret'

        # use memory database, reset entirely every time
        configuration.reload()
        configuration.set('database-path', '')
        configuration.set('debug', True)
        configuration.set('debug-db-reset', True)
        configure_authenticator(self.app)
        configure_database(self.app)

        self.controller = controller
        self.facade = DatabaseFacade()

    def tearDown(self):
        """Called after each test."""
        del self.controller
        del self.facade
        del self.app

    def test_authenticate_not_authenticated(self):
        with self.app.test_request_context():
            self.assertIsNotNone(self.controller.authenticate())

    def test_authenticate_already_authenticated(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertIsNone(self.controller.authenticate())

    def test_submit_result_unauthenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.submit_result, "", "")

    def test_submit_result_malformed_json(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(ValueError, self.controller.submit_result, "---", "")

    def test_submit_result_success(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_standard_user()
            metadata = '{ \
                "uploader": "' + USER["sub"] + '", \
                "benchmark": "name/name:tag", \
                "site": "name" \
            }'
            self.assertTrue(self.controller.submit_result(template, metadata))

    def test_submit_benchmark_unauthenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.submit_benchmark, "", "")

    def test_submit_benchmark_malformed_docker_name(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(RuntimeError, self.controller.submit_benchmark, ":", "")
            self.assertRaises(RuntimeError, self.controller.submit_benchmark, None, "")

    def test_submit_benchmark_success(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertTrue(self.controller.submit_benchmark("rosskukulinski/leaking-app", "submit comment."))
            self.assertTrue(self.controller.submit_benchmark("rosskukulinski/leaking-app:latest", ""))

    def test_submit_benchmark_duplicate(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.controller.submit_benchmark("rosskukulinski/leaking-app", "submit comment.")
            self.assertRaises(RuntimeError, self.controller.submit_benchmark, "rosskukulinski/leaking-app",
                              "submit comment.")

    def test_submit_site_unauthenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.submit_site, "name", "address")

    def test_submit_site_invalid_short_name(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(ValueError, self.controller.submit_site, None, "address")
            self.assertRaises(ValueError, self.controller.submit_site, "", "address")

    def test_submit_site_invalid_address(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(ValueError, self.controller.submit_site, "name", None)
            self.assertRaises(ValueError, self.controller.submit_site, "name", "")

    def test_submit_site_success(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertTrue(self.controller.submit_site("name", "127.0.0.1", "long name", "description"))

    def test_submit_site_duplicate_name(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.controller.submit_site("name", "127.0.0.1")
            self.assertFalse(self.controller.submit_site("name", "127.0.0.2"))

    def test_submit_tag_unauthenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.submit_tag, "tag")

    def test_submit_tag_malformed(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(ValueError, self.controller.submit_tag, None)
            self.assertRaises(ValueError, self.controller.submit_tag, "")

    def test_submit_tag_success(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertTrue(self.controller.submit_tag("tag"))
            self.assertTrue(self.controller.submit_tag("tag2"))

    def test_submit_tag_duplicate(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.controller.submit_tag("tag")
            self.assertFalse(self.controller.submit_tag("tag"))

    def test_get_site_not_found(self):
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_site("name"))

    def test_get_site(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.controller.submit_site("name", "127.0.0.1")
            self.assertEqual(self.controller.get_site("name").get_name(), "name")

    def test_remove_site_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.remove_site, "name")

    def test_remove_site_not_existing(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertFalse(self.controller.remove_site("not existing"))

    def test_remove_site_with_results(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_standard_user()
            metadata = {
                "uploader": USER["sub"],
                "benchmark": "name/name:tag",
                "site": "name"
            }
            self.controller.submit_result(template, json.dumps(metadata))
            self.assertRaises(RuntimeError, self.controller.remove_site, "name")

    def test_remove_site(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertTrue(self.controller.submit_site("name", "127.0.0.1"))
            self.assertTrue(self.controller.remove_site("name"))
            # make sure that site is removed
            self.assertFalse(self.controller.remove_site("name"))

    def test_report_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.report, "{}")

    def test_report_incomplete(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(ValueError, self.controller.report, "{}")

    def test_report_non_existent_object(self):
        with self.app.test_request_context():
            self._login_standard_user()
            report = {
                "type": "site",
                "uploader": USER["sub"],
                "value": "name",
                "message": "msg"
            }
            self.assertRaises(ValueError, self.controller.report, json.dumps(report))

    def test_report(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_standard_user()
            self.controller.submit_site("name", "127.0.0.1")
            report = {
                "type": "site",
                "uploader": USER["sub"],
                "value": "name",
                "message": "msg"
            }
            self.assertTrue(self.controller.report(json.dumps(report)))

    def test_get_report_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.get_report, "uuid")

    def test_get_report_not_admin(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(AuthenticateError, self.controller.get_report, "uuid")

    def test_get_report_non_existent(self):
        with self.app.test_request_context():
            self._login_admin()
            self.assertRaises(DatabaseFacade.NotFoundError, self.controller.get_report, "uuid")

    def test_get_report(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_admin()
            self.controller.submit_site("name", "127.0.0.1")
            report = self.controller.get_reports()[0]
            uuid = report.get_uuid()
            self.assertEqual(uuid, self.controller.get_report(uuid).get_uuid())

    def test_get_reports_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.get_reports)

    def test_get_reports_not_admin(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(AuthenticateError, self.controller.get_reports)

    def test_get_reports_empty(self):
        with self.app.test_request_context():
            self._login_admin()
            self.assertEqual(len(self.controller.get_reports(True)), 0)

    def test_get_reports(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_admin()
            self.controller.submit_site("name", "127.0.0.1")
            report = {
                "type": "site",
                "uploader": USER["sub"],
                "value": "name",
                "message": "msg"
            }
            self.controller.report(json.dumps(report))
            report["message"] = "msg2"
            self.controller.report(json.dumps(report))
            # 3 reports: 2 submitted manually, 1 automatically generated for submitted site
            self.assertEqual(len(self.controller.get_reports(True)), 3)

    def test_process_report_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.process_report, True, "id")

    def test_process_report_not_admin(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(AuthenticateError, self.controller.process_report, True, "id")

    def test_process_report_report_not_exists(self):
        with self.app.test_request_context():
            self._login_admin()
            self.assertEqual(self.controller.process_report(True, "id"), False)

    def test_process_report_site(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_admin()
            self.controller.submit_site("name", "127.0.0.1")
            report = self.controller.get_reports()[0]
            uuid = report.get_uuid()
            self.assertEqual(self.controller.process_report(True, uuid), True)

    def test_process_report_benchmark(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        with self.app.test_request_context():
            self._login_admin()
            self.controller.submit_benchmark("rosskukulinski/leaking-app", "submit comment.")
            report = self.controller.get_reports()[0]
            uuid = report.get_uuid()
            self.assertEqual(self.controller.process_report(True, uuid), True)

    def test_process_report_result(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_admin()
            metadata = '{ \
                "uploader": "' + USER["sub"] + '", \
                "benchmark": "name/name:tag", \
                "site": "name" \
            }'
            self.controller.submit_result(template, metadata)
            filters = {'filters': [
                {'type': 'uploader', 'value': USER["info"]["email"]},
            ]}
            result = self.facade.query_results(json.dumps(filters))[0]
            report = {
                "type": "result",
                "uploader": USER["sub"],
                "value": result.get_uuid(),
                "message": "msg"
            }
            self.controller.report(json.dumps(report))
            reports = self.controller.get_reports()
            result_report = None
            for report in reports:
                if report.get_report_type() == Report.RESULT:
                    result_report = report
            uuid = result_report.get_uuid()
            self.assertTrue(self.controller.process_report(True, uuid), True)

    def test_remove_result_not_authenticated(self):
        with self.app.test_request_context():
            self.assertRaises(AuthenticateError, self.controller.remove_result, "name")

    def test_remove_result_not_admin(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertRaises(AuthenticateError, self.controller.remove_result, "name")

    def test_remove_result_not_found(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_admin()
            metadata = '{ \
                "uploader": "' + USER["sub"] + '", \
                "benchmark": "name/name:tag", \
                "site": "name" \
            }'
            self.controller.submit_result(template, metadata)
            self.assertFalse(self.controller.remove_result("wrong_uuid"))

    def test_remove_result(self):
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_admin()
            metadata = {
                "uploader": USER["sub"],
                "benchmark": "name/name:tag",
                "site": "name"
            }
            self.controller.submit_result(template, json.dumps(metadata))
            filters = {'filters': [
                {'type': 'uploader', 'value': USER["info"]["email"]},
            ]}
            results = self.facade.query_results(json.dumps(filters))
            self.assertEqual(len(results), 1)
            self.assertTrue(self.controller.remove_result(results[0].get_uuid()))
            # make sure that result is now hidden
            results = self.facade.query_results(json.dumps(filters))
            self.assertEqual(len(results), 0)

    def test_add_current_user_if_missing(self):
        with self.app.test_request_context():
            controller._add_current_user_if_missing()
            self.assertRaises(DatabaseFacade.NotFoundError, self.facade.get_uploader, USER['sub'])
            self._login_standard_user()
            controller._add_current_user_if_missing()
            self.assertTrue(self.facade.get_uploader(USER['sub']))
            controller._add_current_user_if_missing()
            self.assertTrue(self.facade.get_uploader(USER['sub']))

    def test_valid_docker_hub_name_fails(self):
        # malformed
        self.assertFalse(self.controller._valid_docker_hub_name(None))
        self.assertFalse(self.controller._valid_docker_hub_name(""))
        self.assertFalse(self.controller._valid_docker_hub_name("Gibberishcfzugiop"))
        # official images are not supported
        self.assertFalse(self.controller._valid_docker_hub_name("mysql"))
        # private image
        self.assertFalse(self.controller._valid_docker_hub_name("thechristophe/example-private"))
        # typos, non existent image, wrong tags etc
        self.assertFalse(self.controller._valid_docker_hub_name("mysql!"))
        self.assertFalse(self.controller._valid_docker_hub_name("mysql:8.0.123"))
        self.assertFalse(self.controller._valid_docker_hub_name("mysql:"))
        self.assertFalse(self.controller._valid_docker_hub_name("rosskukulinsk/leaking-app:latest"))
        self.assertFalse(self.controller._valid_docker_hub_name("rosskukulinski/leakingapp:latest"))
        self.assertFalse(self.controller._valid_docker_hub_name("rosskukulinski/leaking-app:lates"))
        self.assertFalse(self.controller._valid_docker_hub_name("/leaking-app:latest"))
        self.assertFalse(self.controller._valid_docker_hub_name("/:latest"))
        self.assertFalse(self.controller._valid_docker_hub_name("/:"))
        self.assertFalse(self.controller._valid_docker_hub_name(":"))

    def test_valid_docker_hub_name(self):
        self.assertTrue(self.controller._valid_docker_hub_name("rosskukulinski/leaking-app"))
        self.assertTrue(self.controller._valid_docker_hub_name("rosskukulinski/leaking-app:latest"))

    def test_site_result_amount(self):
        self.assertEqual(self.controller._site_result_amount("name"), 0)
        uploader_metadata = '{"id": "' + USER['sub'] + '", "email": "' + USER['info']['email'] + '", "name": "' + \
                            USER['info']['name'] + '"}'
        self.facade.add_uploader(uploader_metadata)
        self.facade.add_benchmark("name/name:tag", USER['sub'])
        self.facade.add_site('{"short_name": "name", "address": "100"  }')
        with self.app.test_request_context():
            with open("eosc_perf/controller/config/result_template.json") as file:
                template = file.read()
            self._login_standard_user()
            metadata = '{ \
                "uploader": "' + USER["sub"] + '", \
                "benchmark": "name/name:tag", \
                "site": "name" \
            }'
            self.controller.submit_result(template, metadata)
            self.assertEqual(self.controller._site_result_amount("name"), 1)

    def test_get_email(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertEqual(self.controller.get_email(), USER["info"]["email"])
            self._logout()
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_email())

    def test_get_full_name(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertEqual(self.controller.get_full_name(), USER["info"]["name"])
            self._logout()
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_full_name())

    def test_get_user_id(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertEqual(self.controller.get_user_id(), USER["sub"])
            self._logout()
        with self.app.test_request_context():
            self.assertIsNone(self.controller.get_user_id())

    def test_is_admin_fail_no_affiliations(self):
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertFalse(self.controller.is_admin())

    def test_is_admin_fail_wrong_affiliations(self):
        with self.app.test_request_context():
            self._login_standard_user()
            session['user']['info']['edu_person_scoped_affiliations'] = ["student@mit.edu"]
            self.assertFalse(self.controller.is_admin())

    def test_is_admin_one_entitlement(self):
        with self.app.test_request_context():
            self._login_admin()
            self.assertTrue(self.controller.is_admin())

    # def test_is_admin_all_affilliations(self):
    #    admin_affiliations = configuration.get('debug_admin_affiliations')
    #    admin_affiliations += ["test@test.edu", "hacker@1337.ccc"]
    #    # Extending admin affiliations
    #    configuration.set("debug_admin_affiliations", admin_affiliations)
    #    with self.app.test_request_context():
    #        # User has all admin affiliations
    #        self._login_standard_user()
    #        session['user']['info']['edu_person_scoped_affiliations'] = admin_affiliations
    #        self.assertTrue(self.controller.is_admin())

    def test_authenticated(self):
        """Tests if IOController returns True when logged
           in during is_authenticated method call"""
        with self.app.test_request_context():
            self._login_standard_user()
            self.assertTrue(self.controller.is_authenticated())

    def test_not_authenticated(self):
        """Tests if IOController returns False when not logged
           in during is_authenticated method call"""
        with self.app.test_request_context():
            self.assertFalse(self.controller.is_authenticated())

    def _login_standard_user(self):
        session['user'] = USER
        session['user']['info'].pop('eduperson_entitlement', None)

    def _login_admin(self):
        self._login_standard_user()
        admin_entitlement = configuration.get('debug_admin_entitlements')[:1]
        admin_entitlement[0] += '#aai.egi.eu'
        session['user']['info']['eduperson_entitlement'] = admin_entitlement

    def _logout(self):
        session.pop('user', None)


if __name__ == '__main__':
    unittest.main()