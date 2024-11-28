$(document).ready(function() {
    function pollDraftState() {
        setInterval(function() {
            $.ajax({
                url: '/get_draft_state/',
                type: 'GET',
                data: { 'league_id': leagueId },
                success: function(response) {
                    if (response.current_turn_user_id === currentUserId) {
                        $('#current-turn').text('It is your turn!');
                        $('button').removeAttr('disabled'); // Enable player selection buttons
                    } else {
                        $('#current-turn').text(response.current_turn_user_name);
                        $('button').attr('disabled', true); // Disable player selection buttons if not the user's turn
                    }
                }
            });
        }, 3000); // Poll every 3 seconds
    }

    pollDraftState();
});
