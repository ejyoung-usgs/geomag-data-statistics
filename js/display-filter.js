function showTime(selection)
{
    var toShow = "delay"+selection.value;
    delays = document.getElementsByClassName("delays");
    for(i = 0; i < delays.length; ++i)
    {
        delays[i].style.display = "none";
        delays[i].style.visibility = "hidden";
    }
    document.getElementById(toShow).style.display="block";
    document.getElementById(toShow).style.visibility="visible";
}
