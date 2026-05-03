# Lab 00: Environment Setup – AWS CLI Configuration

## Participant Lab Guide

**Duration:** 10-15 minutes  
**Difficulty:** Beginner  
**Module:** Pre-Lab / Setup  
**AWS Region:** `us-east-1`

---

## Lab Objective

In this lab, you will configure your AWS credentials on the virtual desktop. This is a **one-time setup** before starting Lab 1.

You will:

- Log into the AWS Console using your IAM credentials
- Create new access keys (and delete any old ones)
- Configure the AWS CLI on your virtual desktop
- Verify that everything works

> **All tools (VS Code, Python, Terraform, AWS CLI, Git) are already installed on your virtual desktop.**

---

## What You Will Build

By the end of this lab, you will have:

- A working AWS CLI configuration on your virtual desktop
- Valid access keys for the AWS CLI
- Verified that your setup is ready for Lab 1

---

## Prerequisites

| Requirement | Status |
| --- | --- |
| Virtual desktop access (provided by instructor) | ✅ |
| AWS IAM username and password (provided by instructor) | ✅ |
| VS Code installed on virtual desktop | ✅ |
| AWS CLI pre-installed | ✅ |

---

# Step-by-Step Instructions

---

## Step 1: Log into the AWS Console

**Tool:** Web browser on your virtual desktop

1. Open a browser (Chrome, Firefox, or Edge).

2. Navigate to the **AWS Console URL** provided by your instructor.

3. Log in using your IAM credentials:

   - **Username:** Provided by your instructor
   - **Password:** Provided by your instructor

   > If this is your first time logging in, you may be prompted to change your password.

✅ **You are now logged into the AWS Console.**

---

## Step 2: Create New Access Keys

**Tool:** AWS Console (browser)

> **Why:** The AWS CLI needs access keys to authenticate your commands. You will create a new pair and delete any old ones.

### 2.1 Navigate to IAM

1. In the AWS Console search bar at the top, type **IAM**.
2. Click **IAM** from the search results.

### 2.2 Find Your User

1. In the left menu, click **Users**.
2. Click on your username (provided by your instructor).

### 2.3 Go to Security Credentials

1. Click the **Security credentials** tab.
2. Scroll down to the **Access keys** section.

### 2.4 Delete Any Existing Keys

> ⚠️ **Important:** Always delete old keys before creating new ones for security reasons.

1. If there are any existing access keys:
   - Click **Actions** → **Delete**
   - Confirm the deletion
   - Click **Deactivate** then **Delete**

### 2.5 Create a New Access Key

1. Click **Create access key**.
2. Select **Command Line Interface (CLI)**.
3. Check the confirmation box at the bottom of the page.
4. Click **Next**.
5. Skip the description tag (optional) and click **Create access key**.

### 2.6 Save Your Access Keys

> ⚠️ **CRITICAL:** You will not see the secret key again. Save it now.

You will see:

```text
Access Key ID: AKIA...
Secret Access Key: ... (a long string)
```

**Save these securely:**

- Copy and paste both keys into a text file (Notepad) on your desktop.
- Or click **Download .csv file** to save them.

**Example of saved credentials:**

```text
Access Key ID: AKIAIOSFODNN7EXAMPLE
Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

✅ **Access keys created successfully.**

---

## Step 3: Open VS Code Terminal

**Tool:** VS Code on your virtual desktop

### 3.1 Launch VS Code

- Click the **VS Code** icon on your desktop or start menu.

### 3.2 Open a Terminal

- In VS Code, click **Terminal** → **New Terminal** from the top menu.

A terminal panel opens at the bottom of VS Code.

---

## Step 4: Configure AWS CLI

**Tool:** VS Code Terminal

> **Note:** The commands below work the same on all operating systems.

### 4.1 Run the Configure Command

In the VS Code terminal, type:

```bash
aws configure
```

### 4.2 Enter Your Credentials

You will be prompted for four pieces of information:

```text
AWS Access Key ID [None]: PASTE_YOUR_ACCESS_KEY_ID
AWS Secret Access Key [None]: PASTE_YOUR_SECRET_KEY
Default region name [None]: us-east-1
Default output format [None]: json
```

**What to enter:**

| Prompt | What to Enter |
| --- | --- |
| AWS Access Key ID | Paste the **Access Key ID** you saved |
| AWS Secret Access Key | Paste the **Secret Access Key** you saved |
| Default region name | `us-east-1` |
| Default output format | `json` |

> **Tip:** When pasting the Secret Access Key, nothing will appear on screen. This is normal.

---

## Step 5: Verify Your Configuration

**Tool:** VS Code Terminal

Run this command to confirm your credentials work:

```bash
aws sts get-caller-identity
```

**Expected output:**

```json
{
    "UserId": "AIDA...",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

✅ **Your AWS CLI is configured correctly.**

> If you see an error, double-check that you copied the Access Key ID and Secret Access Key correctly. Ask your instructor for help if it still fails.

---

## Step 6: Save Your AWS Account ID

**Tool:** VS Code Terminal

You will need your AWS Account ID in Lab 1. Save it now:

```bash
aws sts get-caller-identity --query Account --output text
```

Copy the output (a 12-digit number). Save it in the same text file where you saved your access keys.

**Example:**

```text
123456789012
```

✅ **You have your AWS Account ID saved.**

---

## Lab Completion Checklist

- [ ] Logged into AWS Console
- [ ] Old access keys deleted
- [ ] New access keys created and saved
- [ ] VS Code terminal open
- [ ] `aws configure` completed successfully
- [ ] `aws sts get-caller-identity` shows your account info
- [ ] AWS Account ID saved

---

## 🚨 Troubleshooting

| Issue | Solution |
| --- | --- |
| `aws: command not found` | **Notify instructor** – AWS CLI should be pre-installed |
| `AccessDenied` when running `aws sts get-caller-identity` | Your credentials are incorrect. Run `aws configure` again. |
| Can't find your IAM user in AWS Console | Ask your instructor for your username |
| Forgot to save Secret Access Key | You cannot retrieve it. Delete the key in the console and create a new one. |

---

## 🎯 What You Learned

| Concept | What You Did |
| --- | --- |
| IAM Access Keys | Created and deleted access keys for CLI access |
| AWS CLI | Configured credentials using `aws configure` |
| Verification | Confirmed identity with `aws sts get-caller-identity` |
| Account ID | Retrieved your AWS Account ID for future labs |

---

## ➡️ Next Step

**You are now ready for Lab 1: First SageMaker Training Job.**

Continue to [**Lab 1 — participant guide**](../lab1-first-training/PARTICIPANT_LAB_GUIDE.md) (and the lab overview at [`labs/lab1-first-training/LAB_OVERVIEW.md`](../../labs/lab1-first-training/LAB_OVERVIEW.md)).

---

**🎉 Congratulations! Your environment is configured and ready.**
