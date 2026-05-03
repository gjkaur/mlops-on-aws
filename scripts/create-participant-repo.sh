#!/bin/bash
# create-participant-repo.sh

# Create a clean copy without solution folders
cp -r mlops-on-aws mlops-on-aws-participant
rm -rf mlops-on-aws-participant/solutions

# Remove any instructor notes from Markdown guides (LAB_OVERVIEW, etc.)
find mlops-on-aws-participant -name "*.md" -exec sed -i '/INSTRUCTOR NOTE/d' {} \;

# Create archive
zip -r mlops-on-aws-participant.zip mlops-on-aws-participant
