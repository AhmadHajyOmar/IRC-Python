import os
import subprocess
import time

if __name__ == '__main__':
    try:
        os.remove(os.path.join('servers', '.coverage'))
    except FileNotFoundError:
        pass
    with open('server.log', 'w') as server_log, open('fuzzer.log', 'w') as fuzzer_log:
        print('Starting server... ', end='')
        server = subprocess.Popen(['python', 'server.py'], stdout=server_log, cwd='servers')
        print('ok')
        time.sleep(2)
        print('Starting fuzzer... ', end='')
        fuzzer = subprocess.Popen(['python', 'fuzzer.py'], stdout=fuzzer_log, cwd='fuzzer')
        print('ok')
        print('Fuzz for 60 seconds... ', end='')
        server.wait()
        print('ok')
        try:
            fuzzer.wait(timeout=60)
        except subprocess.TimeoutExpired:
            print('The fuzzer did not properly terminate.')
        print('Writing server stdout to server.log... ', end='')
        server_log.flush()
        print('ok')
        print('Writing fuzzer stdout to fuzzer.log... ', end='')
        fuzzer_log.flush()
        print('ok')
    print()
    subprocess.run(['python', '-m', 'coverage', 'html'], cwd='servers')
        