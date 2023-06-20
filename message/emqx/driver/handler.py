import sys
import subprocess
import os
import digi

if __name__ == '__main__':
    # Default username and password
    emqx_dash_username = os.environ.get("EMQX_DASH_USERNAME", "admin")
    emqx_dash_password = os.environ.get("EMQX_DASH_PASSWORD", "digi_password")

    try:
        # Start EMQX, delete default admin account, delete old configured admin account, create new configured admin account
        subprocess.check_call(f'emqx start; emqx ctl admins del admin; emqx ctl admins del {emqx_dash_username}; emqx ctl admins add {emqx_dash_username} {emqx_dash_password} &', shell=True)
    except subprocess.CalledProcessError:
        digi.logger.fatal("unable to start emqx")
        sys.exit(1)

    digi.logger.info("started emqx")
    digi.run()
