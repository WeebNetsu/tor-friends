$(document).ready(() => {
    $(".show-details").click(function () {
        let text = $(this).text();
        const GAME_ID =
        "#" + text.substr(text.indexOf("for:") + 4, 99).trim();
        //console.log(GAME.length);

        if ($(GAME_ID).hasClass("hidden")) {
        $(GAME_ID).removeClass("hidden");
        $(GAME_ID).addClass("show");
        } else {
        $(GAME_ID).removeClass("show");
        $(GAME_ID).addClass("hidden");
        }
    });

    $(window).keydown(function (event) {
        if (event.keyCode == 13) {
          event.preventDefault();
          return false;
        }
      });
});