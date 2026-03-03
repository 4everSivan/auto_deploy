import ansible_runner
import os
import tempfile
import yaml

inventory = {
    'all': {
        'hosts': {
            '192.168.100.50': {
                'ansible_host': '192.168.100.50',
                'ansible_port': 22,
                'ansible_user': 'fbase',
                'ansible_password': 'fbase',
                'ansible_become': True,
                'ansible_become_user': 'root',
                'ansible_become_password': 'linux123!@#'
            }
        }
    }
}

with tempfile.TemporaryDirectory() as tmpdir:
    inv_path = os.path.join(tmpdir, 'inventory.yml')
    with open(inv_path, 'w') as f:
        yaml.dump(inventory, f)
    
    print(f"Running ansible-runner in {tmpdir}")
    result = ansible_runner.run(
        private_data_dir=tmpdir,
        host_pattern='192.168.100.50',
        module='shell',
        module_args='echo "Hello World"',
        inventory=inv_path,
        envvars={
            'ANSIBLE_HOST_KEY_CHECKING': 'False',
            'ANSIBLE_SSH_ARGS': '-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
        },
        quiet=False
    )
    
    print(f"Status: {result.status}")
    print(f"RC: {result.rc}")
    print("--- STDOUT ---")
    print(result.stdout.read())
    print("--- EVENTS ---")
    for event in result.events:
        print(f"Event: {event.get('event')}")
        if event.get('event') in ['runner_on_unreachable', 'runner_on_failed']:
            print(f"Data: {event.get('event_data')}")
