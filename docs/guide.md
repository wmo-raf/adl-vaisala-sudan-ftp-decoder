---
adl_plugin:
  name: ADL Vaisala Sudan FTP Decoder
  connects_to: FTP decoder for Vaisala AWS message logs
  category: country
  country: Sudan
  country_flag: "🇸🇩"
---
# ADL Vaisala Sudan FTP Decoder

Adds a **decoder** to the [ADL FTP Plugin](https://github.com/wmo-raf/adl-ftp-plugin)
for the message log files that the **Vaisala** automatic weather stations of
the Sudan Meteorological Authority deliver over FTP: one line per received
message, each a receipt timestamp followed by the station's semicolon-separated
`KEY:value` payload and a checksum. With this plugin installed, an ADL FTP/SFTP
connection can select **Vaisala (Sudan)** as its decoder and collect those
files like any other FTP source.

**Repository:** [adl-vaisala-sudan-ftp-decoder](https://github.com/wmo-raf/adl-vaisala-sudan-ftp-decoder)
**Plugin type identifier:** none — this package registers a decoder only (see below)
**Decoder identifier:** `vaisala_sudan` · **Decoder display name:** *Vaisala (Sudan)*
**Connection model:** none of its own — uses the FTP plugin's `NetworkFTP` · **Station link model:** the FTP plugin's `FTPStationLink`

> **About the screenshots.** Every image in this guide is regenerated from
> `docs/screenshots.yml` against a seeded demo instance, so hostnames, station
> names, ids and readings in them are placeholders — not values to copy. The
> field tables are the reference for what to enter.

## Overview

This is a *decoder plugin*: it defines no connection or station link of its
own and never talks to a server. The FTP plugin does the listing and
downloading; this plugin turns each downloaded file into observation records.

```
Vaisala AWS ──▶ message log on FTP server ──▶ ADL FTP Plugin (list, match, download)
                                                     │
                                                     ▼
                                      Vaisala (Sudan) decoder (this plugin)
                                                     │
                                                     ▼
                                  records ──▶ variable mappings ──▶ ADL observations
```

The package registers **no entry in the ADL plugin registry** — only the
decoder — so it never appears in the *Add connection* plugin chooser. The
connection's plugin is *ADL FTP Plugin*; this plugin appears only as an entry
in that connection's **Decoder** list. Everything about hosts, credentials,
paths, listing strategies, downloads and the monitoring screens is documented
in the [ADL FTP Plugin guide](https://github.com/wmo-raf/adl-ftp-plugin/blob/main/docs/guide.md);
this guide covers what is specific to the Sudan message logs.

## Prerequisites

- A running ADL instance with the **ADL FTP Plugin** installed (this plugin
  imports from it and cannot load without it).
- FTP/SFTP access to the server the message logs are written to — host,
  port, account, and the directory holding the files (see the FTP plugin
  guide's prerequisites for the network side).
- The list of Vaisala parameter codes each station transmits (`TAAVG1M`,
  `RHAVG1M`, `PAAVG1M` …) and their units, from the station's Vaisala
  configuration — those codes are the variable names you map.

## Installation

Installed like any ADL plugin — see [Plugin Installation](https://adl-tool.readthedocs.io/en/latest/developer_guide/plugins/plugin_installation.html) for
all methods. Both entries are needed in `plugins.toml`, the FTP plugin first:

```toml
[[plugins]]
name = "ADL FTP Plugin"
git  = "https://github.com/wmo-raf/adl-ftp-plugin.git"
tag  = "0.13.0"

[[plugins]]
name = "ADL Vaisala Sudan FTP Decoder"
git  = "https://github.com/wmo-raf/adl-vaisala-sudan-ftp-decoder.git"
tag  = "0.0.2"
```

After rebuild/restart, confirm both appear in `docker compose exec adl
list-plugins`, and that *Vaisala (Sudan)* is offered in the Decoder list of a
new FTP connection.

## The file format this decoder reads

| Aspect | Expected |
|---|---|
| File name | Not constrained by the decoder. Match it with the station link's *File Pattern*; if the log is rotated with a date in the name, *Filter by Date* can narrow it. |
| Line | `<receipt time>, (<payload>)<checksum>` — for example `2026-01-10 12:21:42.655, (S:ATB012;D:260110;T:141300;TAAVG1M:31.8;RHAVG1M:22;PAAVG1M:1004.3)BB38EB4A`. Blank lines are ignored. A line that does not fit this shape is **silently skipped**. |
| Receipt time | `YYYY-MM-DD HH:MM:SS.fff`, the moment the message reached the logging system. It is carried on the record as `receipt_time` but is not the observation time. |
| Payload | `KEY:value` pairs separated by `;`. `S` is the station id, `D` the observation date as `YYMMDD`, `T` the observation time as `HHMMSS`. Every other key is a Vaisala parameter code; numeric values become numbers. A value of `/` (Vaisala's missing marker) or an empty value drops that key from the record. |
| Kept as text | `S`, `STATUS`, `SENSORSTATUS`, `PTEND3H` are kept as strings, which ADL cannot store as observations (see Troubleshooting). |
| Checksum | The 8 hex characters after the closing bracket. Read but **not verified**. |
| Observation time | `D` + `T`, read as the station's local time (the connection's *Stations Timezone*, or the station link's own). A line without both `D` and `T` produces a record with no observation time, which ADL rejects. |

Every message line becomes one record keyed by its parameter codes, so a
file holding 24 hourly messages yields 24 records.

## Connection configuration

Create a **Network FTP/SFTP** connection exactly as the FTP plugin guide
describes (connection type, host, port, username, password, passive mode,
timeout), then:

| Field | Value for this source |
|---|---|
| Decoder | **Vaisala (Sudan)** |
| CSV Configuration | Leave empty — this decoder needs no configuration. |
| Variable Mappings | One row per Vaisala parameter code to store (below). Connection-level mappings apply to every station on the connection; use station-level mappings (FTP plugin guide) for a station whose codes differ. |

![FTP connection form with the decoder selected](images/vaisala_sudan_connection_form.png)

### Variable mappings

| Field | Description |
|---|---|
| ADL Parameter | The ADL `DataParameter` the values are stored under. |
| File Variable Name | The Vaisala parameter code **exactly** as it appears in the payload, e.g. `TAAVG1M`. Codes are case-sensitive. |
| File Variable Unit | The unit the station transmits that code in (from its Vaisala configuration); ADL converts to the ADL parameter's unit. |

**Example (illustrative codes — use the ones in your messages):** ADL
Parameter `Air Temperature` ← File Variable Name `TAAVG1M`, unit `degC`; ADL
Parameter `Pressure` ← `PAAVG1M`, unit `hPa`.

The FTP plugin's **Test Decoder Configuration** action on the connection row
decodes one uploaded log file and shows the records — the quickest way to
read the codes off a real file before typing the mappings.

![Connection-level variable mappings](images/vaisala_sudan_variable_mappings.png)

## Station link configuration

Create an **FTP/SFTP Station Link** per station (all fields are the FTP
plugin's; only the values matter here):

| Field | Value for this source |
|---|---|
| Remote Path | The directory the message logs are written into. |
| File Pattern | A glob selecting one station's log, e.g. `ATB012_*.log`. |
| Directory Structured by Date | Off, unless the logging system nests directories by date on your server. |
| File Listing Strategy | **Pattern Only** for a single running log; **Filter by Date** with the matching *Filename Date Format* if the log is rotated with a date in the name. This decoder does no date narrowing of its own. |
| Collection Start Date | Messages older than this are rejected by ADL even when the file is fetched. Set it for a backfill. |
| Skip downloading already downloaded files | **Off** for a running log that grows through the day, so it is re-downloaded each run (already-saved messages are not duplicated); on for rotated logs that are written once. |

![Station link form](images/vaisala_sudan_station_link_form.png)

## Admin UI added by this plugin

None. This plugin adds no page, menu entry, button or form of its own; the
only place it appears is as an option in the FTP connection's *Decoder*
select. The FTP plugin's own surfaces — *Test Decoder Configuration*, the
*Direct Fetch Files* preview, the *FTP station data files* list — work with
this decoder and are documented in the FTP plugin guide.

## Data collection behavior

One run, per enabled station link:

1. The FTP plugin lists *Remote Path* and keeps the names matching *File
   Pattern* (narrowed by file-name date under *Filter by Date*).
2. Each file not yet held (or every file, with *Skip downloading already
   downloaded files* off) is downloaded and handed to this decoder.
3. The decoder reads the file line by line, parses each message's payload
   into `code → number`, builds the observation time from `D` and `T`, and
   yields one record per message. Malformed lines are skipped without a
   message.
4. ADL applies the variable mappings and unit conversion and stores the
   values; a message already stored is updated, not duplicated.

- **Timezones:** `D`/`T` are read as local station time; the station's
  timezone (connection default or per-link) is what ADL stamps them with.
  The receipt time is not used.
- **Backfill:** set *Collection Start Date* before the first run.

## Source checks / diagnostics

All monitoring for a connection using this decoder is the FTP plugin's: the
**Ingestion Diagnostic** page proves the FTP host, port and account, and the
station link's **Station Source Check** proves the resolved remote path and
counts the files matching the pattern. How to read both screens is covered in
[Monitoring & Diagnostics](https://adl-tool.readthedocs.io/en/latest/user_guide/monitoring_and_diagnostics.html);
their FTP-specific messages are catalogued in the FTP plugin guide. This
plugin adds no check of its own — a file that lists and downloads fine but
decodes to nothing shows up as a **warning in the task log** with a zero
*values saved* count, not in the source checks.

![Ingestion Diagnostic page for the FTP connection](images/vaisala_sudan_ingestion_diagnostic.png)

![Station Source Check on the station link](images/vaisala_sudan_station_source_check.png)

![FTP station data files list](images/vaisala_sudan_data_files.png)

### Feedback catalogue — messages involving this decoder

The decoder itself logs nothing; what an operator sees comes from the FTP
plugin's pipeline and from ADL core's record validation, in the station's
activity log or task log:

| Message (example) | Where | Meaning | What to do |
|---|---|---|---|
| `File ATB012.log decoded 0 record(s) but none of its values were saved — check the variable mappings and the ingestion window` | task log (warning) | No line in the file fit the `<time>, (<payload>)<checksum>` shape, so every line was skipped silently. | Open the file; compare a line with the example above (spaces after the comma, the brackets, the 8-hex checksum). |
| `File ATB012.log decoded 24 record(s) but none of its values were saved — …` | task log (warning) | Messages parsed, but no mapped code matched, or all of them lie before *Collection Start Date*. | Use *Test Decoder Configuration* to see the emitted codes; check the start date. |
| `Bad record for station …: 1 validation error for StationRecordModel observation_time` | task log (warning) | A message had no `D` or `T` pair, so the record has no observation time. | Check the station's message template; those lines carry no observation. |
| `Rejected observation 2026-01-10 14:13:00+02:00 for station …: before the collection start date …` | task log (warning) | Normal on a backfill file that reaches further back than the start date. | Nothing, or move the start date back. |
| `Error decoding file …: 'utf-8' codec can't decode byte …` | task log (error) | The file is not UTF-8 (the decoder opens it strictly). | Check the logging system's encoding; a binary or Latin-1 file cannot be read by this release. |
| `Resolved remote path /vaisala: 0 file(s) matching 'ATB012_*.log'.` | Station Source Check (OK) | The FTP plugin's station check: path found, nothing matches right now. | Check the pattern and that the log exists on the server. |

## Troubleshooting

**Every file decodes to 0 records**
: The line shape differs from what the decoder expects — most often the
  space after the comma or the checksum length. Lines are skipped without any
  message, so the only symptom is the zero count. Use *Test Decoder
  Configuration* with a copied line to confirm.

**A parameter is never stored although it is in every message**
: Its value is `/` (missing) in every message, or the code is one of `S`,
  `STATUS`, `SENSORSTATUS`, `PTEND3H`, which this release keeps as text — ADL
  stores numbers only. Pressure tendency (`PTEND3H`) therefore cannot be
  ingested with 0.0.2.

**Observation times are shifted by a few hours**
: `D`/`T` are read in the station's timezone. Check the connection's *Stations
  Timezone* and the station link's override; if the AWS transmits UTC, set the
  timezone to UTC.

**A running log stops updating in ADL after the first fetch**
: *Skip downloading already downloaded files* is on. Turn it off for a
  growing log.

## Compatibility

| Plugin version | Requires | Notes |
|---|---|---|
| 0.0.2 | ADL FTP Plugin (imports its decoder registry; written against 0.13.0), ADL core 0.8.x | Current release. Uses the base decoder's file matching, so it accepts the dated `get_matching_files()` call of FTP plugin 0.10.0 and later. |

## Changelog

See [GitHub Releases](https://github.com/wmo-raf/adl-vaisala-sudan-ftp-decoder/releases).
