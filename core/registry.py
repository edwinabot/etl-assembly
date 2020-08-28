from typing import Union
from datetime import datetime, timezone

from core.database import TemplateTable, UserConfTable, JobTable, get_table
from core.logs import get_logger

logger = get_logger(__name__)


class ActiveRecordMixin:
    @classmethod
    def _setup_table(cls):
        cls._table = get_table(cls.table_definition)

    @classmethod
    def _get_by_id(cls, _id):
        logger.debug(f"getting by id {_id}")
        response = cls._table.get_item(Key={"id": _id})
        if "Item" not in response:
            raise ValueError(f"No record found with id '{_id}' in {cls._table.name}")
        item = response["Item"]
        logger.debug(f"Found {item}")
        return item

    @classmethod
    def get(cls, _id=None):
        if not any((_id,)):
            raise ValueError("No query lookups provided")
        try:
            cls._setup_table()
            if _id:
                return cls._get_by_id(_id)
        except Exception as ex:
            logger.error(f"{ex}")
            raise


class Template(ActiveRecordMixin):
    table_definition = TemplateTable

    def __init__(self, _id, extract, transform, load):
        self.extract = extract
        self.transform = transform
        self.load = load
        self.id = _id

    @classmethod
    def _get_by_id(cls, _id):
        item = super()._get_by_id(_id)
        return cls(
            _id=item["id"],
            extract=item["extract"],
            transform=item["transform"],
            load=item["load"],
        )


class UserConf(ActiveRecordMixin):
    """
    UserConf is a lazy object that contains all user related data
    to configurations of a Job.
    """

    table_definition = UserConfTable

    def __init__(
        self,
        _id,
        source_conf,
        destination_conf,
        trustar_user_id,
        created_at,
        updated_at,
    ):
        """
        {
            "created_at": "2020-06-01T17:30:00Z",
            "destination_conf": {
                "trustar_api": "https://api.trustar.co/"
            },
            "destination_secrets": {
                "key": "secretkey",
                "secret": "secretcert"
            },
            "id": "2a87d9ac-e242-454d-9407-e5601ceb0519",
            "source_conf": {
                "frequency": "60",
                "url": "http://mispbox.com"
            },
            "source_secrets": {
                "cert": "secretcert",
                "key": "secretkey"
            },
            "trustar_user_id": "6c0305fd-e121-43a1-841f-06acc75ede7f",
            "updated_at": "2020-08-01T14:13:33Z"
        }
        """
        self._id = _id
        self._source_conf = source_conf
        self._destination_conf = destination_conf
        self._trustar_user_id = trustar_user_id
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def id(self):
        return self._id

    @property
    def source_conf(self):
        return self._source_conf

    @property
    def destination_conf(self):
        return self._destination_conf

    @property
    def source_secrets(self):
        # We will retrieve from database everytime...
        # I don't want this to linger in memory too much time
        response = self._table.get_item(Key={"id": self._id})
        item = response["Item"]
        return item.get("source_secrets")

    @property
    def destination_secrets(self):
        # We will retrieve from database everytime...
        # I don't want this to linger in memory too much time
        response = self._table.get_item(Key={"id": self._id})
        item = response["Item"]
        return item.get("destination_secrets")

    @classmethod
    def _get_by_id(cls, _id):
        item = super()._get_by_id(_id)
        return cls(
            _id=item.get("id"),
            source_conf=item.get("source_conf"),
            destination_conf=item.get("destination_conf"),
            trustar_user_id=item.get("trustar_user_id"),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
        )


class Job(ActiveRecordMixin):
    table_definition = JobTable

    def __init__(
        self,
        _id,
        template: Union[str, Template],
        user_conf: Union[str, UserConf],
        last_run: Union[str, datetime],  # TODO: this can be None cause never ran
        name: str,
        description: str,
    ):
        if not all((_id, user_conf, template)):
            raise ValueError("Arguments can't be None")
        if not isinstance(template, (Template, str)):
            raise TypeError("template arg must be of type Template or str")
        if not isinstance(user_conf, (UserConf, str)):
            raise TypeError("user_conf arg must be of type Template or str")

        self._id = _id
        self._template = template
        self._user_conf = user_conf
        self.name = name
        self.description = description
        if last_run and isinstance(last_run, str):
            self._last_run = datetime.fromisoformat(last_run)
        elif last_run and isinstance(last_run, datetime):
            if not datetime.tzinfo:
                raise TypeError("last_run must be offset-aware datetime")
            self._last_run = last_run
        else:
            self._last_run = datetime.now(timezone.utc)

    @property
    def id(self):
        return self._id

    @property
    def template(self):
        """
        Lazy attribute for template
        """
        if isinstance(self._template, str):
            # Mock object
            self._template = Template.get(_id=self._template)
        return self._template

    @property
    def user_conf(self):
        """
        Lazy attribute for user conf
        """
        if isinstance(self._user_conf, str):
            self._user_conf = UserConf.get(_id=self._user_conf)
        return self._user_conf

    @property
    def last_run(self):
        if self._last_run and isinstance(self._last_run, str):
            self._last_run = datetime.fromisoformat(self._last_run)
        return self._last_run

    @last_run.setter
    def last_run(self, new_datetime: datetime):
        """
        Set a new datetime for last_run
        """

        # check that new datetime is more recent that last run
        if self.last_run and self.last_run > new_datetime:
            raise Exception(f"{new_datetime} is previous to {self._last_run}")

        self._last_run = new_datetime

    @classmethod
    def _get_by_id(cls, _id):
        item = super()._get_by_id(_id)
        return cls(
            _id=item.get("id"),
            template=item.get("template"),
            user_conf=item.get("user_conf"),
            last_run=item.get("last_run")
            if "last_run" in item and item.get("last_run")
            else None,
            name=item.get("name", ""),
            description=item.get("description", ""),
        )

    def save(self):
        # TODO: abstract this method
        """
        State information are attributes of the Job... should go to job configs...
        Does Job Configs name makes sense still?
        Probably Job is the right one
        What about storing run info for each step? A table for run summaries?
        """

        results = self._table.update_item(
            Key={"id": self.id},
            UpdateExpression="SET last_run = :last_run",
            ExpressionAttributeValues={":last_run": self.last_run.isoformat()},
            ReturnValues="UPDATED_NEW",
        )
        logger.debug(f"Updated job {self.id} with values {results}")
