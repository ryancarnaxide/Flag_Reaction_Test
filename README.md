# Flag_Reaction_Test

main = stable demo-ready code
dev = active development branch

Make sure to always pull from dev before starting to work:
git checkout dev
git pull origin dev

Workflow: Make feature branches off of dev branch and then we can use pull requests to merge updates

Example:

git checkout dev        # get dev branch
git pull origin dev     # make sure it’s up to date
git checkout -b feature/csv-export   # create new branch

...make changes while on feature branch, for example make changes to file app.py...

git add app.py
git commit -m "Added CSV export button"
git push origin feature/csv-export

Then open a Pull Request on GitHub to merge feature/csv-export → dev.
OR
git checkout dev
git pull origin dev
git merge feature/csv-export
git push origin dev


Merging updates from dev → main:
Again either open a Pull request on GitHub and merge dev → main
OR
git checkout main
git pull origin main
git merge dev
git push origin main


