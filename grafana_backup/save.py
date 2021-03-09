from grafana_backup.api_checks import main as api_checks
from grafana_backup.save_dashboards import main as save_dashboards
from grafana_backup.save_datasources import main as save_datasources
from grafana_backup.save_folders import main as save_folders
from grafana_backup.save_alert_channels import main as save_alert_channels
from grafana_backup.archive import main as archive
from grafana_backup.save_orgs import main as save_orgs
from grafana_backup.save_users import main as save_users
import sys
import os.path
from os import path
import shutil

def main(args, settings):
    arg_components = args.get('--components', False)
    arg_no_archive = args.get('--no-archive', False) or (not settings.get('ARCHIVE_OUTPUT'))

    backup_functions = {'dashboards': save_dashboards,
                        'datasources': save_datasources,
                        'folders': save_folders,
                        'alert-channels': save_alert_channels,
                        'organizations': save_orgs,
                        'users': save_users}

    (status, json_resp, uid_support, paging_support) = api_checks(settings)

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        print("server status is not ok: {0}".format(json_resp))
        sys.exit(1)

    settings.update({'UID_SUPPORT': uid_support})
    settings.update({'PAGING_SUPPORT': paging_support})

    if settings.get('TIMESTAMP_OUTPUT') == False:
        # If we are not timestamping outputs, we should delete any existing output files before generating new ones
        # However we don't want to just delete the whole directory since there may be, e.g. a .git directory in there
        backup_dir = settings.get('BACKUP_DIR')
        print("{0} exists - deleting contents before creating new non-timestamped backup.".format(backup_dir))
        # Special-case /alert_channels vs alert-channels in the backup_functions list
        if path.exists(backup_dir + '/alert_channels' ):
            shutil.rmtree(backup_dir + '/alert_channels')
        for subdir in backup_functions.keys():
            if path.exists(backup_dir + '/' + subdir ):
                shutil.rmtree(backup_dir + '/' + subdir)

    if arg_components:
        arg_components_list = arg_components.split(',')

        # Backup only the components that provided via an argument
        for backup_function in arg_components_list:
            backup_functions[backup_function](args, settings)
    else:
        # Backup every component
        for backup_function in backup_functions.keys():
            backup_functions[backup_function](args, settings)

    aws_s3_bucket_name = settings.get('AWS_S3_BUCKET_NAME')

    if not arg_no_archive:
        archive(args, settings)
