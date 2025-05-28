from git import Repo

class GitInspector:
    def __init__(self, repo_path="."):
        self.repo = Repo(repo_path)

    def get_last_commit_diff(self):
        diff = self.repo.git.diff('HEAD~1', 'HEAD')
        return diff

    def get_commit_message(self, n=1):
        return list(self.repo.iter_commits('HEAD', max_count=n))[0].message

    def get_changed_files(self, n=1):
        commit = list(self.repo.iter_commits('HEAD', max_count=n))[0]
        return [f.a_path for f in commit.diff(None)]

    def blame_file(self, path):
        return self.repo.git.blame(path)