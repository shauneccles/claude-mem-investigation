# April cohort — sample of the April 13 calendar week

13,546 stars in the Monday-Sunday calendar week. 13.1% throwaway-shape (0 repos + 0 followers). 1.2% of accounts were created within 24 hours of starring. 0.78% within one hour.

Below is a random sample of accounts from that cohort where the account was less than one day old when it starred the repo.

| login | created UTC | starred UTC | gap | followers | repos |
|---|---|---|---|---|---|
| `odyssey-work` | 2026-04-13 01:12:00 | 2026-04-13 01:30:51 | 0.3 h | 0 | 1 |
| `kauaesyt20-prog` | 2026-04-12 21:12:22 | 2026-04-13 01:40:58 | 4.5 h | 0 | 0 |
| `brendawong-max` | 2026-04-13 03:46:38 | 2026-04-13 04:17:55 | 0.5 h | 1 | 0 |
| `leonardobernardo199824-jpg` | 2026-04-13 01:29:04 | 2026-04-13 05:09:12 | 3.7 h | 0 | 1 |
| `blockbirdbot-hub` | 2026-04-13 01:37:42 | 2026-04-13 05:57:24 | 4.3 h | 0 | 0 |
| `SNOKJB` | 2026-04-12 10:10:20 | 2026-04-13 05:58:58 | 19.8 h | 0 | 0 |
| `NoahC963-jpg` | 2026-04-12 18:58:44 | 2026-04-13 06:47:16 | 11.8 h | 0 | 1 |
| `qq1834639311-cloud` | 2026-04-13 01:35:31 | 2026-04-13 07:14:55 | 5.7 h | 0 | 0 |
| `gogmad-Ghub` | 2026-04-12 19:11:41 | 2026-04-13 09:14:44 | 14.1 h | 2 | 0 |
| `kaingaji-cyber` | 2026-04-12 19:23:35 | 2026-04-13 09:45:27 | 14.4 h | 1 | 1 |

## The pattern

Every account in this sample has 0 or 1 public repo, 0–2 followers, and was created within a few hours of when it starred the repo. The login-naming scheme is the tell:

- `odyssey-**work**`, `kauaesyt20-**prog**`, `brendawong-**max**`, `leonardobernardo199824-**jpg**`, `blockbirdbot-**hub**`, `NoahC963-**jpg**`, `qq1834639311-**cloud**`, `gogmad-**Ghub**`, `kaingaji-**cyber**`

Inventory of observed suffixes across the full April 13 calendar-week cohort: `-work`, `-prog`, `-max`, `-jpg`, `-hub`, `-cyber`, `-cloud`, `-web`, `-pixel`, `-Ghub`.

The suffix pattern looks consistent with dictionary-plus-suffix account generation — a script or workflow concatenating a base noun/name with one of a small pool of suffixes. I wouldn't expect organic users to show this pattern this consistently.

The 5-account same-hour cluster at `2026-04-16T05Z`:

- `dwala1983zuma-pixel`
- `lawnthings`
- `yashdeeparya939-cyber`
- `GoykD`
- `reddameronasiempresiempre-web`

Three of five match the suffix pattern (`-pixel`, `-cyber`, `-web`); the other two are short random strings.

## Reproducing this list

```bash
cd scripts
python analyze_stars.py --sample-cohort 2026-04-13 2026-04-19 --age-max-days 1
```

Or by hand, with the jsonl decompressed:

```bash
zcat evidence/stargazers/stars-graphql.jsonl.gz \
 | python3 -c '
import sys, json
for line in sys.stdin:
    e = json.loads(line)
    s = e["starredAt"][:10]
    if "2026-04-13" <= s <= "2026-04-19":
        from datetime import datetime
        c = datetime.fromisoformat(e["node"]["createdAt"].replace("Z","+00:00"))
        st = datetime.fromisoformat(e["starredAt"].replace("Z","+00:00"))
        if (st - c).total_seconds() < 86400:
            print(e["node"]["login"], e["node"]["createdAt"], e["starredAt"],
                  e["node"]["followers"]["totalCount"], e["node"]["repositories"]["totalCount"])
'
```
