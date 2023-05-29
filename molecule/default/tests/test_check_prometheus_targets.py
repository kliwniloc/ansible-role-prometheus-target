testinfra_hosts = ['prometheus']


def test_check_hosts_added(host):
    t1 = host.file('/opt/target1.yml')
    t2 = host.file('/opt/target2.yml')
    t3 = host.file('/opt/target3.yml')

    assert t1.exists
    assert t2.exists
    assert t3.exists

    assert '    - application' in t1.content_string
    assert '    - test1' in t2.content_string
    assert '    - test2' in t2.content_string
    assert '    - application_AA' in t3.content_string
