#!/usr/bin/env python3
import os
import subprocess
import grp
import getpass

def check_permissions():
    """Check if the user has the necessary permissions to run the application."""
    print("🔍 Checking permissions...")

    # Check for read access to /dev/input/event*
    try:
        # Check if user is in the 'input' group
        input_gid = grp.getgrnam('input').gr_gid
        user_groups = os.getgrouplist(getpass.getuser(), os.getgid())

        if input_gid in user_groups:
            print("✅ User is in the 'input' group.")
        else:
            print("❌ User is not in the 'input' group.")
            print("   This is required for mouse detection to work.")
            print("   Please run the following command to add the user to the 'input' group:")
            print(f"   sudo usermod -a -G input {getpass.getuser()}")
            print("   You will need to log out and log back in for the changes to take effect.")
            return False

    except KeyError:
        print("⚠️  The 'input' group does not exist on this system.")
        print("   Mouse detection may not work correctly.")
        print("   Please consult your distribution's documentation for information on input device permissions.")
        return False

    print("✅ Permissions seem to be configured correctly.")
    return True

if __name__ == "__main__":
    check_permissions()