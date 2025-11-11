# Raspberry Pi Docker Container Installation


# make sure apt is up to date
sudo apt update
sudo apt upgrade -y

# docker prerequisites
sudo apt install -y ca-certificates curl gnupg

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

# add docker repository to apt
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/debian \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update

# install docker from apt
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin



# install git (if you haven’t already)
sudo apt install -y git

# clone the repository
git clone --branch feature/react-ui-docker --single-branch https://github.com/ryancarnaxide/Flag_Reaction_Test

cd Flag_Reaction_Test

# build the image
sudo apt install -y docker-compose-plugin
sudo docker compose up -d

# run application with firefox
firefox http://localhost:5173