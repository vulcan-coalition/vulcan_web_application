from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from pydrive.files import ApiRequestError, FileNotDownloadableError
from collections import deque
import os

drive = None


def initialize():
    global drive
    gauth = GoogleAuth(settings_file="artifacts/settings.yaml")
    # Try to load saved client credentials
    gauth.LoadCredentialsFile("artifacts/credentials.json")
    if gauth.credentials is None:
        # Authenticate if they're not there
        gauth.CommandLineAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()
    # Save the current credentials to a file
    drive = GoogleDrive(gauth)


def resolveFolderId(path, root="root"):
    parent = root
    if len(path) == 0:
        return parent
    path = path.split("/")
    for folder in path:
        filelist = drive.ListFile({"q": f"title = '{folder}' and '{parent}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"}).GetList()
        if len(filelist) == 0:  # folder not found
            print("Folder not found")
            return None
        parent = filelist[0]["id"]
    return parent


def listFolder(drive_root, folder, folderOnly=False):
    fid = resolveFolderId(folder, drive_root)
    return listFoldersByID(fid, folderOnly)


def listFoldersByID(id, folderOnly=False):
    if folderOnly:
        filelist = drive.ListFile({"q": f"'{id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"}).GetList()
    else:
        filelist = drive.ListFile({"q": f"'{id}' in parents and trashed = false"}).GetList()
    return filelist


def downloadFolder(drive_root, src, dst):
    parent, folder = os.path.split(src)
    parent = resolveFolderId(parent, drive_root)
    filelist = drive.ListFile({"q": f"title = '{folder}' and '{parent}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"}).GetList()
    if len(filelist) == 0:  # folder not found
        print("Folder not found")
        return False
    folderId = filelist[0]['id']
    path = os.path.join(dst, folder)
    q = deque()
    q.append({"id": folderId, "path": path})
    while len(q) > 0:
        elm = q.pop()
        folderId = elm['id']
        path = elm['path']
        os.makedirs(path, exist_ok=True)
        filelist = drive.ListFile({"q": f"'{folderId}' in parents and trashed = false"}).GetList()
        for file in filelist:
            if file['mimeType'] == "application/vnd.google-apps.folder":
                q.append({"id": file["id"], "path": os.path.join(path, file['title'])})
            else:
                local_path = os.path.join(path, file['title'])
                try:
                    print(f"Downloading {local_path}")
                    file.GetContentFile(local_path)
                except ApiRequestError:
                    print("Failed to download", local_path)
                    return False
                except FileNotDownloadableError:
                    print("Skipping file", local_path)
    return True


def uploadFolder(drive_root, src, dst):
    parent = resolveFolderId(dst, drive_root)
    title = os.path.basename(src)
    driveFile = drive.CreateFile({"title": title, "parents": [{"id": parent}], "mimeType": "application/vnd.google-apps.folder"})
    try:
        driveFile.Upload()
    except ApiRequestError as e:
        print(e, parent)
        return False
    q = deque()
    q.append({"title": title, "path": src, "id": driveFile["id"]})
    while len(q) > 0:
        elm = q.pop()
        title = elm["title"]
        parent = elm["id"]
        path = elm["path"]
        for file in os.listdir(path):
            innerPath = os.path.join(path, file)
            if os.path.isdir(innerPath):
                driveFile = drive.CreateFile({"title": file, "parents": [{"id": parent}], "mimeType": "application/vnd.google-apps.folder"})
                try:
                    driveFile.Upload()
                except ApiRequestError as e:
                    print(e, innerPath)
                    return False
                q.append({"title": file, "path": innerPath, "id": driveFile["id"]})
            else:
                driveFile = drive.CreateFile({"title": file, "parents": [{"id": parent}]})
                driveFile.SetContentFile(innerPath)
                print(f"Uploading {innerPath}")
                try:
                    driveFile.Upload()
                except ApiRequestError as e:
                    print(e, innerPath)
                    return False
    return True


def uploadFile(drive_root, src, dst, new_name=None):
    # usage: uploadFile("root", "./README.md", "test")
    parent = resolveFolderId(dst, drive_root)
    title = os.path.basename(src) if new_name is None else new_name

    driveFile = drive.CreateFile({"title": title, "parents": [{"id": parent}]})
    driveFile.SetContentFile(src)
    print(f"Uploading {src}")
    try:
        driveFile.Upload()
    except ApiRequestError as e:
        print(e, src)
        return False
    return True


if __name__ == '__main__':

    initialize()

    gList = listFolder("root", "", folderOnly=True)
    print([x['title'] for x in gList])

    gList = listFoldersByID("root")
    print([x['title'] for x in gList])

    uploadFile("root", "./README.md", "test", new_name="local_readme.md")
