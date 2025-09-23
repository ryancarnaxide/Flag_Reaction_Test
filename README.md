# Flag_Reaction_Test

Ensure Git is installed on your laptop. If not installed go to https://git-scm.com/downloads and download and run installer based on your OS  
After accepting collaborator invite  
1. Open VS Code (or your terminal)  
2. Navigate to the folder where you want the repo to live  
3. Run:  
git clone https://github.com/ryancarnaxide/Flag_Reaction_Test.git  
cd Flag_Reaction_Test  

Your local repository will now be setup and you will be defaulted to the main branch  

main branch = stable demo-ready code  
dev branch = active development branch  

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


