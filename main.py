"""
This gets run as a cron job. Periodically run and reauthenticte the user's AWS and ECR
from a Vault token. 
"""

import asyncio
import aiofiles
import base64
import time

from common import settings, asyncio_utils, properties, log

import boto3


async def ensure_auth(hvac, role):
    """ Check the current authentication state of the system, including AWS and Docker.

    SSH is not included here, since its developer-only.
    """
    if role == 'snowbot':
        role = 'robot'

    last_aws_auth = settings.hatch.aws_auth_time
    hours = (time.time() - last_aws_auth) / 3600
    log.verbose(f'Hours since last AWS auth: {hours}')

    if hours > properties.aws_auth_period or True:
        if not await auth_aws(hvac, role):
            return

        settings.reload()
        settings.hatch.aws_auth_time = time.time()
        settings.save()

    # Docker
    last_docker_auth = settings.hatch.docker_auth_time
    hours = (time.time() - last_docker_auth) / 3600
    log.verbose(f'Hours since last Docker auth: {hours}')

    if hours > properties.docker_auth_period or True:
        if not await auth_docker():
            return

        settings.reload()
        settings.hatch.docker_auth_time = time.time()
        settings.save()

    # SSH keys
    if not await ssh_key_valid():
        await sign_ssh_key(hvac)


async def auth_docker():
    """ Authenticate the HOSTS docker daemon """
    boto_client = boto3.client('ecr')

    try:
        future = asyncio.get_event_loop().run_in_executor(None, boto_client.get_authorization_token)
        res = await asyncio.wait_for(future, 10)
    except Exception as e:
        return log.error(f"Unable to authenticate with AWS ECR: {e}")

    # Also has an expiresAt key
    token = res['authorizationData'][0]['authorizationToken'].encode('utf-8')
    username, password = base64.b64decode(token).decode('utf-8').split(':')
    endpoint = '778747430246.dkr.ecr.us-east-2.amazonaws.com'

    command = f'docker login {endpoint} --username AWS --password {password}'
    ret = await asyncio_utils.stream_subprocess(command, log.verbose, log.verbose, timeout=20)

    if ret != 0:
        return log.error('Unable to authenticate docker')

    log.verbose('Authenticated with docker')
    return True


async def auth_aws(hvac, role):
    """ Get an AWS token save it to the system.

    boto is not async-friendly, but this call must be.

    Role is one of pct, robot, developer.
    """
    try:
        future = asyncio.get_event_loop().run_in_executor(None, lambda: hvac.write(f'aws/sts/{role}', ttl='36h'))
        token = await asyncio.wait_for(future, 10)
    except Exception as e:
        log.error(f"Failed to authenticate hvac: {e}")
        return False

    creds = f"[default]\naws_access_key_id = {token['data']['access_key']}\naws_secret_access_key = " + \
        f"{token['data']['secret_key']}\naws_security_token = {token['data']['security_token']}\n"

    async with aiofiles.open('/app/.aws/credentials', "w") as f:
        await f.write(creds)

    async with aiofiles.open('/app/.aws/config', "w") as f:
        await f.write('[default]\nregion = us-east-2\noutput = json\n')

    log.verbose(f'Authenticated with aws as {role}')
    return True


if __name__ == '__main__':
    print("Authdaemon starting...")
