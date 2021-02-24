(function() {
    $("#file-type-general").on("change", function () {
        if (this.value == "Video") {
          $("#file-type-minor").html(`
            <option>Video</option>
            <option selected>Movie</option>
            `);
    
          $("#file-type-minor").prop("disabled", false);
        } else if (this.value == "Game" || this.value == "Application") {
          $("#file-type-minor").html(`
            <option selected>Windows</option>
            <option>Mac</option>
            <option>Linux</option>
            <option>Android</option>
            <option>iOS</option>
            `);
    
          $("#file-type-minor").prop("disabled", false);
        } else {
          $("#file-type-minor").prop("disabled", true);
        }
    });
    
    $("#description").keypress(function(){
        $("#count").text($("#description").val().length+1);
    })
})();