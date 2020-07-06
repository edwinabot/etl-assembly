fixtures = {
    "etl_assembly_templates": [
        {
            "destination": "trustar",
            "extract": "from_events",
            "id": "5b132e9d-4d85-4845-804a-c54deb2bafa6",
            "load": "load_reports",
            "source": "misp",
            "transform": "for_trustar_reports",
        }
    ],
    "etl_assembly_job_configs": [
        {
            "id": "7f9010e3-f1b9-408a-8fbf-85fe20f8fd34",
            "template": "5b132e9d-4d85-4845-804a-c54deb2bafa6",
            "user_conf": "2a87d9ac-e242-454d-9407-e5601ceb0519",
        }
    ],
    "etl_assembly_user_configs": [
        {
            "created_at": "2020-06-01T17:30:00Z",
            "destination_conf": {"trustar_api": "https://api.trustar.co/"},
            "destination_secrets": {"key": "secretkey", "secret": "secretcert"},
            "id": "2a87d9ac-e242-454d-9407-e5601ceb0519",
            "source_conf": {"frequency": "60", "url": "http://mispbox.com"},
            "source_secrets": {"cert": "secretcert", "key": "secretkey"},
            "trustar_user_id": "6c0305fd-e121-43a1-841f-06acc75ede7f",
            "updated_at": "2020-08-01T14:13:33Z",
        }
    ],
}
