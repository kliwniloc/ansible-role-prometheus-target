import yaml


testinfra_hosts = ["prometheus"]


def read_file(host, path):
    target = host.file(path)
    assert target.exists
    return target


def read_yaml_file(host, path):
    return yaml.safe_load(read_file(host, path).content_string)


def test_lineinfile_bootstrap_adds_first_host_without_breaking_yaml(host):
    target = read_file(host, "/opt/lineinfile_first_host.yml")

    assert target.user == "prometheus"
    assert target.group == "prometheus"
    assert target.mode == 0o600
    assert read_yaml_file(host, "/opt/lineinfile_first_host.yml") == ["application:9100"]


def test_lineinfile_adds_subsequent_host_to_existing_yaml(host):
    target = read_file(host, "/opt/lineinfile_bootstrap.yml")

    assert target.content_string == (
        "- labels:\n"
        "    my: label\n"
        "  targets:\n"
        "  - existing:9100\n"
        "  - application:9100\n"
    )

    assert read_yaml_file(host, "/opt/lineinfile_bootstrap.yml") == [
        {"labels": {"my": "label"}, "targets": ["existing:9100", "application:9100"]}
    ]


def test_lineinfile_parallel_writes_keep_all_hosts_and_parse(host):
    hosts = sorted(read_yaml_file(host, "/opt/lineinfile_parallel.yml"))
    assert hosts == [
        "application2:9100",
        "application3:9100",
        "application4:9100",
        "application:9100",
    ]


def test_lineinfile_user_edited_file_stays_parseable(host):
    target = read_file(host, "/opt/lineinfile_user_edited.yml")

    assert target.content_string == (
        "# user comment\n"
        "- labels:\n"
        "    env: prod\n"
        "  targets:\n"
        "  - existing:9100\n"
        "  - application2:9100\n"
    )

    assert read_yaml_file(host, "/opt/lineinfile_user_edited.yml") == [
        {"labels": {"env": "prod"}, "targets": ["existing:9100", "application2:9100"]}
    ]


def test_lineinfile_removing_last_host_still_leaves_parseable_yaml(host):
    assert read_yaml_file(host, "/opt/lineinfile_remove_last.yml") == [
        {"labels": {"env": "stage"}, "targets": None}
    ]


def test_lineinfile_compatibility_simple_and_prefix_cases(host):
    assert read_yaml_file(host, "/opt/simple_target1.yml") == ["application"]
    assert read_yaml_file(host, "/opt/simple_target2.yml") == ["test1", "test2"]
    assert read_yaml_file(host, "/opt/simple_target3.yml") == ["application_AA"]
    assert read_yaml_file(host, "/opt/simple_target4.yml") == ["exporter_without_id"]
    assert read_yaml_file(host, "/opt/prefix_target1.yml") == ["application"]
    assert read_yaml_file(host, "/opt/prefix_target2.yml") == ["application"]
    assert read_yaml_file(host, "/opt/prefix/prefix_target3.yml") == ["application"]


def test_lineinfile_hooks_still_run(host):
    assert sorted(read_yaml_file(host, "/opt/hook_target.yml")) == [
        "application",
        "application2",
        "application3",
        "application4",
    ]

    assert host.file("/opt/hook1").exists
    assert host.file("/opt/hook2").content_string == "hello\nhello\nhello\nhello\n"
