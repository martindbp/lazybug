<template>
    <div>
        <div v-for="event in learnEvents">
            {{ event }}
        </div>

        <div v-for="session in log">
            Session time: {{ session.sessionTime }}
            Caption id: {{ session.captionId }}
            Caption hash: {{ session.captionHash }}
            Events:
            <div v-for="event in session.events">
                {{ reverseEventsMap(event[0]) }}: {{ event.slice(1) }}
            </div>
        </div>
    </div>
</template>

<script>
export default {
    props: {
    },
    data: function() { return {
        log: null,
    }},
    mounted: function() {
        const self = this;
        getLog(function(data) {
            self.log = data;
        });
    },
    methods: {
        reverseEventsMap: function(eventId) {
            return reverseEventsMap[eventId];
        }
    },
    watch: {
    },
    computed: {
        learnEvents: function() {
            const learnEvents = [];
            if (this.log === null) return learnEvents;

            for (const session of this.log) {
                for (const event of session.events) {
                    if (reverseEventsMap[event[0]].startsWith("EVENT_LEARN")) {
                        learnEvents.push(event);
                    }
                }
            }

            return learnEvents;
        },
    },
};
</script>

<style>
</style>
