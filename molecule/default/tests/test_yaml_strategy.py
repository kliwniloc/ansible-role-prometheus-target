import yaml


testinfra_hosts = ["prometheus"]


def read_yaml_file(host, path):
    target = host.file(path)
    assert target.exists
    return yaml.safe_load(target.content_string)


def get_group_by_labels(groups, labels):
    for group in groups:
        if group.get("labels", {}) == labels:
            return group
    raise AssertionError(f"Missing target group with labels {labels!r}")


def get_unlabeled_group(groups):
    for group in groups:
        if group.get("labels", {}) == {}:
            return group
    raise AssertionError("Missing unlabeled target group")


def has_group_with_labels(groups, labels):
    return any(group.get("labels", {}) == labels for group in groups)


def test_yaml_bootstrap_adds_first_host_to_empty_file(host):
    assert read_yaml_file(host, "/opt/yaml_bootstrap.yml") == [
        {"labels": {"job": "node"}, "targets": ["application:9100"]}
    ]


def test_yaml_parallel_writes_keep_all_hosts_in_same_group(host):
    groups = read_yaml_file(host, "/opt/yaml_parallel.yml")
    assert get_group_by_labels(groups, {"job": "node"})["targets"] == [
        "existing:9100",
        "application:9100",
        "application2:9100",
        "application3:9100",
        "application4:9100",
    ]


def test_yaml_user_edited_file_is_reparsed_and_keeps_expected_semantics(host):
    groups = read_yaml_file(host, "/opt/yaml_user_edited.yml")

    assert get_group_by_labels(groups, {"severity": "warning", "job": "external"})[
        "targets"
    ] == ["existing_host1:9100", "application2:9100"]

    assert get_group_by_labels(groups, {"severity": "critical", "team": "blue"})[
        "targets"
    ] == ["application2:9200"]

    assert get_unlabeled_group(groups)["targets"] == ["unlabeled:9100", "standalone:9300"]


def test_yaml_moving_host_removes_last_host_from_old_group(host):
    groups = read_yaml_file(host, "/opt/yaml_move_remove_last.yml")

    assert not has_group_with_labels(groups, {"job": "old"})
    assert get_group_by_labels(groups, {"job": "new"})["targets"] == ["application:9400"]


def test_yaml_output_remains_parseable_after_all_operations(host):
    for path in [
        "/opt/yaml_bootstrap.yml",
        "/opt/yaml_parallel.yml",
        "/opt/yaml_user_edited.yml",
        "/opt/yaml_move_remove_last.yml",
        "/opt/yaml_branch_matrix.yml",
        "/opt/yaml_missing_labeled.yml",
        "/opt/yaml_missing_unlabeled.yml",
    ]:
        assert read_yaml_file(host, path) is not None


def test_yaml_branch_matrix_covers_exact_match_and_append(host):
    groups = read_yaml_file(host, "/opt/yaml_branch_matrix.yml")

    assert get_group_by_labels(groups, {"job": "append", "env": "prod"})["targets"] == [
        "existing_append:9500",
        "application3:9506",
    ]

    assert get_group_by_labels(groups, {"job": "present", "env": "prod"})["targets"] == [
        "application3:9501"
    ]


def test_yaml_branch_matrix_keeps_nonmatching_groups_for_both_label_mismatch_paths(host):
    groups = read_yaml_file(host, "/opt/yaml_branch_matrix.yml")

    assert get_group_by_labels(groups, {"job": "wrong", "env": "prod"})["targets"] == [
        "keep_same_length:9500"
    ]

    assert get_group_by_labels(groups, {"job": "short"})["targets"] == [
        "keep_length_mismatch:9500"
    ]

    assert get_group_by_labels(groups, {"job": "foreign"})["targets"] == ["foreign:9505"]


def test_yaml_branch_matrix_moves_hosts_and_drops_emptied_groups(host):
    groups = read_yaml_file(host, "/opt/yaml_branch_matrix.yml")

    assert not has_group_with_labels(groups, {"job": "move_source"})

    assert get_group_by_labels(groups, {"job": "move_target"})["targets"] == [
        "application3:9502"
    ]

    assert get_group_by_labels(groups, {"job": "promoted"})["targets"] == [
        "orphan_unlabeled:9503"
    ]


def test_yaml_branch_matrix_preserves_unlabeled_group_when_targets_remain(host):
    groups = read_yaml_file(host, "/opt/yaml_branch_matrix.yml")

    assert get_unlabeled_group(groups)["targets"] == [
        "shared_unlabeled:9504",
        "standalone_branch:9504",
    ]


def test_yaml_branch_matrix_creates_missing_file_groups_for_labeled_and_unlabeled_targets(host):
    assert read_yaml_file(host, "/opt/yaml_missing_labeled.yml") == [
        {"labels": {"team": "infra"}, "targets": ["application4:9600"]}
    ]

    assert read_yaml_file(host, "/opt/yaml_missing_unlabeled.yml") == [
        {"targets": ["application4:9601"]}
    ]
