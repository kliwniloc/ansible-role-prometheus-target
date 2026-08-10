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


def test_lineinfile_exporter_defaults_overrides_and_duplicates(host):
    assert read_yaml_file(host, "/opt/lineinfile_defaults.yml") == [
        "inherited-default",
        "appended-default",
    ]
    assert read_yaml_file(host, "/opt/lineinfile_no_id.yml") == ["no-id"]
    assert read_yaml_file(host, "/opt/lineinfile_override.yml") == ["item-override"]
    assert read_yaml_file(host, "/opt/lineinfile-prefix/default-prefix.yml") == [
        "prefixed-default"
    ]


def test_lineinfile_skip_default_exporters(host):
    assert read_file(host, "/opt/lineinfile_skipped.yml").content_string == ""


def test_handler_run_once_and_per_host_modes(host):
    for application in ["application", "application2", "application3", "application4"]:
        assert host.file(f"/tmp/command-handler-{application}").exists

    assert host.file("/tmp/shell-handler-run-once").exists


def test_disabled_handlers_do_not_run(host):
    assert not host.file("/tmp/disabled-command-handler").exists
    assert not host.file("/tmp/disabled-shell-handler").exists


def test_lineinfile_absent_removes_exporters(host):
    assert read_yaml_file(host, "/opt/lineinfile_state_removal.yml") == [
        {
            "labels": {"job": "shared"},
            "targets": ["keep:9100"],
        },
        {"labels": {"job": "remove_last"}, "targets": None},
    ]
    assert not host.file("/opt/lineinfile_state_missing.yml").exists
