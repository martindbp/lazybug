#! /bin/bash
inotifywait --quiet --monitor  \
  --event modify \
  --event create \
  --format '%w' browser_extension/components/ |  stdbuf -oL uniq | \
while IFS= read -r file; do
    vue build browser_extension/components/CaptionManager.vue -t lib -d browser_extension/dist
done
