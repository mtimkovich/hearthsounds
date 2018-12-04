# HearthSounds

Get sounds from Hearthstone cards.

Sounds are stored on [Google Storage](https://cloud.google.com/storage/) at
`gs://hearthsounds`. [HearthstoneJSON](https://hearthstonejson.com/) is used
to get card data.

## Setup

```shell
gsutil ls gs://hearthsounds | sed 's#.*/##' > hs_storage.csv
sqlite3 hs_storage.db < hs_storage.sql
```

This caches the sound file directory for faster lookup.
