from grafana_backup.create_org import main as create_org
from grafana_backup.api_checks import main as api_checks
from grafana_backup.create_folder import main as create_folder
from grafana_backup.update_folder_permissions import main as update_folder_permissions
from grafana_backup.create_datasource import main as create_datasource
from grafana_backup.create_dashboard import main as create_dashboard
from grafana_backup.create_alert_channel import main as create_alert_channel
from grafana_backup.create_user import main as create_user
from glob import glob
import sys, tarfile, tempfile, os, shutil, fnmatch, collections


def main(args, settings):
    arg_archive_file = args.get('<archive_file>', None)
    arg_components = args.get('--components', False)
    aws_s3_bucket_name = settings.get('AWS_S3_BUCKET_NAME')

    (status, json_resp, uid_support, paging_support) = api_checks(settings)

    # Do not continue if API is unavailable or token is not valid
    if not status == 200:
        print("server status is not ok: {0}".format(json_resp))
        sys.exit(1)

    # If the archive file given is actually an already untarred (or never tarred) directory...
    if os.path.isdir(arg_archive_file) and os.path.exists(arg_archive_file):
        restore_from_dir(args, arg_components, settings, arg_archive_file)

    else:
        try:
            tarfile.is_tarfile(name=arg_archive_file)
        except IOError as e:
            print(str(e))
            sys.exit(1)
        try:
            tar = tarfile.open(name=arg_archive_file, mode='r:gz')
        except Exception as e:
            print(str(e))
            sys.exit(1)

def restore_components(args, settings, restore_functions, tmpdir):
    arg_components = args.get('--components', False)

    if arg_components:
        arg_components_list = arg_components.split(',')

        # Restore only the components that provided via an argument
        # but must also exist in extracted archive
        for ext in arg_components_list:
            if sys.version_info >= (3,):
                for file_path in glob('{0}/**/*.{1}'.format(tmpdir, ext[:-1]), recursive=True):
                    print('restoring {0}: {1}'.format(ext, file_path))
                    restore_functions[ext[:-1]](args, settings, file_path)
            else:
                for root, dirnames, filenames in os.walk('{0}'.format(tmpdir)):
                    for filename in fnmatch.filter(filenames, '*.{0}'.format(ext[:-1])):
                        file_path = os.path.join(root, filename)
                        print('restoring {0}: {1}'.format(ext, file_path))
                        restore_functions[ext[:-1]](args, settings, file_path)
    else:
        # Restore every component included in extracted archive
        for ext in restore_functions.keys():
            if sys.version_info >= (3,):
                for file_path in glob('{0}/**/*.{1}'.format(tmpdir, ext), recursive=True):
                    print('restoring {0}: {1}'.format(ext, file_path))
                    restore_functions[ext](args, settings, file_path)
            else:
                for root, dirnames, filenames in os.walk('{0}'.format(tmpdir)):
                    for filename in fnmatch.filter(filenames, '*.{0}'.format(ext)):
                        file_path = os.path.join(root, filename)
                        print('restoring {0}: {1}'.format(ext, file_path))
                        restore_functions[ext](args, settings, file_path)

def restore_from_dir(args, arg_components, settings, restore_dir):

    restore_functions = { 'folder': create_folder,
                            'folder_permissions': update_folder_permissions,
                            'datasource': create_datasource,
                            'dashboard': create_dashboard,
                            'alert_channel': create_alert_channel,
                            'organization': create_org,
                            'user': create_user}

    if arg_components:
        arg_components_list = arg_components.split(',')

        # Restore only the components that provided via an argument
        # but must also exist in extracted archive
        for ext in arg_components_list:
            for file_path in glob('{0}/**/*.{1}'.format(restore_dir, ext[:-1]), recursive=True):
                print('restoring {0}: {1}'.format(ext, file_path))
                restore_functions[ext[:-1]](args, settings, file_path)
    else:
        # Restore every component included in extracted archive
        for ext in restore_functions.keys():
            for file_path in glob('{0}/**/*.{1}'.format(restore_dir, ext), recursive=True):
                print('restoring {0}: {1}'.format(ext, file_path))
                restore_functions[ext](args, settings, file_path)
