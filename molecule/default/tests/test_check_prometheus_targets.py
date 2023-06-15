testinfra_hosts = ['prometheus']

"""
Test functionality of defining exporters and default fallbacks
"""
def test_check_hosts_added_simple(host):
    t1 = host.file('/opt/simple_target1.yml')
    t2 = host.file('/opt/simple_target2.yml')
    t3 = host.file('/opt/simple_target3.yml')
    t4 = host.file('/opt/simple_target4.yml')

    assert t1.exists
    assert t2.exists
    assert t3.exists
    assert t4.exists

    assert t1.content_string == \
        '    - application\n'


    assert t2.content_string == \
        '    - test1\n' \
        '    - test2\n'

    assert t3.content_string == \
        '    - application_AA\n'

    assert t4.content_string == \
        '    - exporter_without_id\n'

"""
Test prefix functionality
"""
def test_check_hosts_added_prefix(host):
    t1 = host.file('/opt/prefix_target1.yml')
    t2 = host.file('/opt/prefix_target2.yml')
    t3 = host.file('/opt/prefix/prefix_target3.yml')

    assert t1.exists
    assert t2.exists
    assert t3.exists

    assert t1.content_string == \
        '    - application\n'


    assert t2.content_string == \
        '    - application\n'

    assert t3.content_string == \
        '    - application\n'

"""
Test hook functionality
"""
def test_check_hosts_added_hooks(host):
    t1 = host.file('/opt/hook_target.yml')
    t2 = host.file('/opt/hook1')
    t3 = host.file('/opt/hook2')

    assert t1.content_string == \
        '    - application\n'

    assert t2.exists
    assert t3.exists


"""
Test lineinfile strategy parameters
"""
def test_check_host_added_lineinfile(host):
    t1 = host.file('/opt/lineinfile.yml')

    assert t1.user == 'prometheus'
    assert t1.group == 'prometheus'
    assert t1.mode == 0o600

    assert t1.content_string == \
        '- labels:\n' \
        '    my: label\n' \
        '  targets:\n' \
        '  - existing:9100\n' \
        '  - application:9100\n'
