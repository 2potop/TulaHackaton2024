document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        events: '/get_medication_schedule', // Route to get medication schedule events
        dateClick: function(info) {
            alert('Date: ' + info.dateStr);
        }
    });
    calendar.render();
});
