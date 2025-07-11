#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from airflow.models import Connection
from airflow.models.dag import DAG
from airflow.providers.github.operators.github import GithubOperator
from airflow.utils import timezone

DEFAULT_DATE = timezone.datetime(2017, 1, 1)
github_client_mock = Mock(name="github_client_for_test")


class TestGithubOperator:
    # TODO: Potential performance issue, converted setup_class to a setup_connections function level fixture
    @pytest.fixture(autouse=True)
    def setup_connections(self, create_connection_without_db):
        create_connection_without_db(
            Connection(
                conn_id="github_default",
                conn_type="github",
                password="my-access-token",
                host="https://mygithub.com/api/v3",
            )
        )

    def setup_class(self):
        args = {"owner": "airflow", "start_date": DEFAULT_DATE}
        dag = DAG("test_dag_id", schedule=None, default_args=args)
        self.dag = dag

    def test_operator_init_with_optional_args(self):
        github_operator = GithubOperator(
            task_id="github_list_repos",
            github_method="get_user",
        )

        assert github_operator.github_method_args == {}
        assert github_operator.result_processor is None

    @pytest.mark.db_test
    @patch(
        "airflow.providers.github.hooks.github.GithubClient", autospec=True, return_value=github_client_mock
    )
    def test_find_repos(self, github_mock):
        class MockRepository:
            pass

        repo = MockRepository()
        repo.full_name = "apache/airflow"

        github_mock.return_value.get_repo.return_value = repo

        github_operator = GithubOperator(
            task_id="github-test",
            github_method="get_repo",
            github_method_args={"full_name_or_id": "apache/airflow"},
            result_processor=lambda r: r.full_name,
            dag=self.dag,
        )

        github_operator.run(start_date=DEFAULT_DATE, end_date=DEFAULT_DATE, ignore_ti_state=True)

        assert github_mock.called
        assert github_mock.return_value.get_repo.called
