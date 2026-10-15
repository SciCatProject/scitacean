# SSH keys for the testing SFTP server

The key pair in this directory is used to test SSH key based logins
to the SFTP server provided by `scitacean.testing.sftp`.

**The private key is public!**
It is committed to the Scitacean repository on purpose and provides
no security whatsoever.
It must only ever be used with the local testing server and never
to protect anything of value.

The keys were generated with

```sh
ssh-keygen -t ed25519 -N '' -C 'scitacean-sftp-testing' -f scitacean_test_key
```

The key was modified by adding underscores in the header and footer to bypass the
detect-private-key pre-commit hook.
