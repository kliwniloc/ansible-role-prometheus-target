Ansible Role: Prometheus Target
===============================

An Ansible role for deploying Prometheus targets right from your playbooks.

Installation
------------

via galaxy:

```sh
ansible-galaxy install kliwniloc.prometheus_target
```

```yaml
# requirements.yml
- src: kliwniloc.prometheus_target
```

via git:

```sh
ansible-galaxy install git+https://github.com/kliwniloc/ansible-role-prometheus-target.git,master
```

```yaml
# requirements.yml
- src: https://github.com/kliwniloc/ansible-role-prometheus-target
  name: kliwniloc.prometheus_target
```

Role Variables
--------------

For more details see [`defaults/main.yml`](defaults/main.yml)

You need to specify your Prometheus server. The server needs to be present under
that that name in your inventory.

```yaml
prometheus_target_host: "" # Required
```

You should configure defaults for the exporters you are commonly using.
You can configure this in the `prometheus_target_exporter_defaults` variable.
For example if you're using a single target file for node exporters you may
add the path to that file as a default for the node exporter.
This helps keep the `prometheus_target_exporter` variable clean.

Anything configured in the `prometheus_target_exporter` takes precedence over
the defaults.

```yaml
prometheus_target_exporter_defaults: {}
  # node_exporter:
  #   path: /opt/prometheus/targets.yml
  #   host: '{{ inventory_hostname }}:9100'
  # blackbox_exporter:
  #   path: /opt/targets/blackbox.yml
  #   host: 'https://{{ hostvars[inventory_hostname].ansible_host }}'
  #   path_prefix: ''

prometheus_target_exporter: []
```

You can also add exporter that you want to have deployed without needing to
specify them in the `prometheus_target_exporter` variable by adding them to the
`prometheus_target_default_exporters` variable.

```yaml
prometheus_target_default_exporters: []
prometheus_target_skip_default_exporters: false
```

As you usually have most target files in one directory you can specify a target
prefix for your target files:

```yaml
prometheus_target_exporter_target_prefix: ''
```

This way you only need to pass `target.yml` instead of `/path/to/target.yml` as
your exporter path. You can additionally define this at the
`prometheus_target_exporter_defaults` and the `prometheus_target_exporter` level
using the `path_prefix` variable:

```yaml
prometheus_target_exporter_defaults:
  blackbox_exporter:
    path: /opt/targets/blackbox.yml
    host: 'https://{{ hostvars[inventory_hostname].ansible_host }}'
    path_prefix: '' # Disables configured prefix
```

This role offers a few strategies that you can use to deploy your targets.
The strategy decides how exactly targets are added to the targets file and more
importantly how to handle existing configuration.

* `lineinfile` is the default strategy and simply *appends* a line to the target
  file if it isn't already there.
* `yaml` *parses* the yaml target file and adds the host to it. This might mess
  with the readability of your yaml file, and you should avoid it if you edit
  the yaml file manually as well.
* `json` *parses* the json target file and adds the host to it.

```yaml
prometheus_target_strategy: lineinfile
```

`lineinfile` simply uses the Ansible
[lineinfile](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/lineinfile_module.html)
module to append a line to the specified targets file. This is usually enough to
deploy targets and does not change any of the existing lines of the
configuration which is nice if you comment your target files.

You can configure a prefix and suffix for applying the target to your target
file. The defaults are configured to add a list with 2 (2 space) indentation
levels.

```yaml
prometheus_target_strategy_lineinfile_prefix: '    - '
prometheus_target_strategy_lineinfile_suffix: ''
```

So the target file should look something like this:

```diff
  - labels:
      my: label
    targets:
+     - host:9100
```

There are a few handlers that are notified if a new target is added. You will
want to use those to reload your Prometheus instance after adding modifying
targets. If you manage your target files in git you may also wish to commit the
changes via a hook.

You can enable or disable the handlers via the `prometheus_target_handler_command_enabled`/
`prometheus_target_handler_shell_enabled` variables and configure become
behavior via `prometheus_target_handler_command_become*`/
`prometheus_target_handler_shell_become*`.

To run the hook per play instead of per hosts, meaning it only runs once, you
can set the `prometheus_target_handler_command_run_once` /
`prometheus_target_handler_shell_run_once` hooks to `true`.

The `prometheus_target_handler_command` and `prometheus_target_handler_shell`
variables map the options of their respective Ansible
[command](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/command_module.html)
and
[shell](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/shell_module.html)
module.

```yaml
prometheus_target_handler_command_enabled: false
prometheus_target_handler_command_become: true
# prometheus_target_handler_command_become_method:
# prometheus_target_handler_command_become_user:
prometheus_target_handler_command_run_once: false
prometheus_target_handler_command: {}

prometheus_target_handler_shell_enabled: false
prometheus_target_handler_shell_become: true
# prometheus_target_handler_shell_become_method:
# prometheus_target_handler_shell_become_user:
prometheus_target_handler_shell_run_once: false
prometheus_target_handler_shell: {}
```

Example Playbooks
-----------------

Simple example

```yaml
- name: Deploy node exporter
  hosts: myhost

  vars: # General configuration. Can be set in group_vars
    prometheus_target_host: prometheus
    prometheus_target_exporter_defaults:
      node_exporter:
        path: /opt/prometheus/targets/node.yml
        host: '{{ inventory_hostname }}:9100'

  roles:
    - role: prometheus.node_exporter # deploy node_exporter service
    - role: kliwniloc.prometheus_target # deploy target
      prometheus_target_exporter:
        - id: node_exporter
```

Using Target prefix

```yaml
- name: Deploy node exporter with target prefix
  hosts: myhost

  vars: # General configuration. Can be set in group_vars
    prometheus_target_host: prometheus
    prometheus_target_exporter_target_prefix: /opt/prometheus/targets/
    prometheus_target_exporter_defaults:
      node_exporter:
        path: node.yml
        host: '{{ inventory_hostname }}:9100'
      blackbox_exporter: # Another exporter with different prefix
        path: target.yml
        host: '{{ inventory_hostname }}'
        path_prefix: /opt/prefix/

  roles:
    - role: kliwniloc.prometheus_target
      prometheus_target_exporter:
        - id: node_exporter # -> /opt/prometheus/targets/node.yml
        - { id: node_exporter, path: /target.yml, path_prefix: '' } # -> /target.yml
        - { id: blackbox_exporter, path: blackbox.yml } # -> /opt/prefix/blackbox.yml
```

Using Handlers

```yaml
- name: Deploy node exporter and reload Prometheus Docker container
  hosts: myhost

  vars: # General configuration. Can be set in group_vars
    prometheus_target_host: prometheus
    prometheus_target_exporter_defaults:
      node_exporter:
        path: /opt/prometheus/targets/node.yml
        host: '{{ inventory_hostname }}:9100'
    prometheus_target_handler_command_enabled: true
    prometheus_target_handler_command_cmd: docker kill -s SIGHUP prometheus

  roles:
    - role: prometheus.node_exporter # deploy node_exporter service
    - role: kliwniloc.prometheus_target # deploy target
      prometheus_target_exporter: [{ id: node_exporter }]
```

Multiple exporters

```yaml
- name: Deploy monitoring
  hosts: mycluster

  vars: # General configuration. Can be set in group_vars
    prometheus_target_host: prometheus
    prometheus_target_exporter_defaults:
      node_exporter:
        path: /opt/prometheus/targets/node.yml
        host: '{{ inventory_hostname }}:9100'
      blackbox_exporter:
        path: /opt/prometheus/targets/blackbox.yml
        host: 'https://{{ hostvars[inventory_hostname].ansible_host }}'

  roles:
    - role: prometheus.node_exporter # deploy node_exporter service
    - role: some_application # deploy web app for blackbox exporter
    - role: kliwniloc.prometheus_target # deploy targets
      prometheus_target_exporter:
        - id: node_exporter # deploy node_exporter with default host
        # deploy an exporter that is not specified in prometheus_target_exporter_defaults
        - { host: exporter_without_id, path: /opt/simple_target4.yml }
        # deploy blackbox_exporter with multiple hosts
        - { id: blackbox_exporter, host: node1.example.org }
        - { id: blackbox_exporter, host: node2.example.org }
        - { id: blackbox_exporter, host: node3.example.org }
```

Target file matching based on group vars

```ini
# Inventory file
[agents_s]
agent-s-[1:2]

[agents_m]
agent-m-[1:2]

[agents:children]
agents_s
agents_m
```

```yaml
# group_vars/agents_s.yml
prometheus_target_exporter_defaults:
    node_exporter:
    path: /opt/prometheus/targets/agent_s.yml
    host: '{{ inventory_hostname }}:9100'

# group_vars/agents_m.yml
prometheus_target_exporter_defaults:
    node_exporter:
    path: /opt/prometheus/targets/agent_m.yml
    host: '{{ inventory_hostname }}:9100'
```

```yaml
- name: Deploy monitoring
  hosts: agents

  vars:
    prometheus_target_host: prometheus

  roles:
    - role: prometheus.node_exporter # deploy node_exporter service
    - role: kliwniloc.prometheus_target
      prometheus_target_exporter:
        - id: node_exporter
```

```diff
# /opt/prometheus/targets/agent_s.yml
+    - agent-s-1:9100
+    - agent-s-2:9100

# /opt/prometheus/targets/agent_m.yml
+    - agent-m-1:9100
+    - agent-m-2:9100
```

Troubleshooting
---------------

* **Running into locks using handlers**

  By default, the handler runs for every host that is changed. This can cause
  issues with locking mechanisms when two hooks run simultaneously.
  A common example of this is when trying to commit the changes to a repository
  on the Prometheus host like this:

  ```yaml
  prometheus_target_handler_shell_enabled: true
  prometheus_target_handler_shell:
      chdir: /opt/monitoring
      cmd: |
          git add prometheus/targets
          git commit -m "[ANSIBLE] Add target"
          git push
  ```

  When deploying targets on multiple hosts you might get an error like this:

  ```txt
  fatal: [application -> prometheus]: FAILED! => {"changed": true, "cmd": "git add prometheus/targets\ngit commit -m \"[ANSIBLE] Add target\"\ngit push\n", "delta": "0:00:00.159961", "end": "2023-10-04 17:14:22.711445", "msg": "non-zero return code", "rc": 1, "start": "2023-10-04 17:14:22.551484", "stderr": "remote: error: cannot lock ref 'refs/heads/master': is at 8b37e6aead861cf15a8726b3cfb48ae6dd9d98e6 but expected b372bb8bac22770f241c41efdc9e7a3581060053        \nTo ssh://git_repository\n ! [remote rejected] master -> master (failed to update ref)\nerror: failed to push some refs to 'ssh://git_repository'", "stderr_lines": ["remote: error: cannot lock ref 'refs/heads/master': is at 8b37e6aead861cf15a8726b3cfb48ae6dd9d98e6 but expected b372bb8bac22770f241c41efdc9e7a3581060053        ", "To ssh://git_repository", " ! [remote rejected] master -> master (failed to update ref)", "error: failed to push some refs to 'ssh://git_repository'"], "stdout": "[master 8b37e6a] [ANSIBLE] Add target\n 1 file changed, 3 insertions", "stdout_lines": ["[master 8b37e6a] [ANSIBLE] Add target", " 1 file changed, 3 insertions"]}
  ```

  To fix this issue you can use the `run_once` options on the handler like
  this:

  ```yaml
  prometheus_target_handler_shell_enabled: true
  prometheus_target_handler_shell_run_once: true
  prometheus_target_handler_shell:
      chdir: /opt/monitoring
      cmd: |
          git add prometheus/targets
          git commit -m "[ANSIBLE] Add target"
          git push
  ```

* **Running into the OpenSSH Max Open Connections limit:**

  SSH Servers often limit the maximum amount of sessions that may be active /
  may be currently activating. When deploying the Prometheus target to a large
  amount of hosts (with many Ansible forks like `-f 100`), the role will make
  an SSH connection to the Prometheus server for each host, and you can get
  an error like this:

  ```txt
  failed: [application -> prometheus] (item={'id': 'agent'}) => {"ansible_loop_var": "item", "item": {"id": "agent"}, "msg": "Data could not be sent to remote host \"prometheus\". Make sure this host can be reached over ssh: mux_client_request_session: session request failed: Session open refused by peer\r\nkex_exchange_identification: read: Connection reset by peer\r\nConnection reset by 0.0.0.0 port 22\r\n", "unreachable": true}
  fatal: [application -> {{ prometheus_target_host }}]: UNREACHABLE! => {"changed": false, "msg": "All items completed", "results": [{"ansible_loop_var": "item", "item": {"id": "agent"}, "msg": "Data could not be sent to remote host \"prometheus\". Make sure this host can be reached over ssh: mux_client_request_session: session request failed: Session open refused by peer\r\nkex_exchange_identification: read: Connection reset by peer\r\nConnection reset by 0.0.0.0 port 22\r\n", "unreachable": true}]}
  ```

  A quick workaround is to just limit the forks of your `ansible-playbook`
  command to something that won't overload your server like this:
  `ansible-playbook -f 1 playbook.yml`.

  To permanently fix the issue you can increase the `MaxSession` and
  `MaxStartups` values in your `sshd_config` of the Prometheus host.

  ```man
  MaxSessions
      Specifies the maximum number of open shell, login or subsystem
      (e.g. sftp) sessions permitted per network connection.  Multiple
      sessions may be established by clients that support connection
      multiplexing.  Setting MaxSessions to 1 will effectively disable
      session multiplexing, whereas setting it to 0 will prevent all
      shell, login and subsystem sessions while still permitting for-
      warding.  The default is 10.

  MaxStartups
      Specifies the maximum number of **concurrent   unauthenticated con-
      nections to the SSH daemon.**  Additional connections will be
      dropped until authentication succeeds or the LoginGraceTime
      expires for a connection.  The default is 10:30:100.

      Alternatively, random early drop can be enabled by specifying the
      three colon separated values ``start:rate:full'' (e.g.
      "10:30:60").  sshd(8) will refuse connection attempts with a
      probability of ``rate/100'' (30%) if there are currently
      ``start'' (10) unauthenticated connections.  The probability
      increases linearly and all connection attempts are refused if the
      number of unauthenticated connections reaches ``full'' (60).
  ```

Dependencies
------------

None.

License
-------

MIT
