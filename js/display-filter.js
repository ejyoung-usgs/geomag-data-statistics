function showTime(selection)
{
    var toShow = "delay"+selection.value;
    delays = document.getElementsByClassName("delays");
    for(i = 0; i < delays.length; ++i)
    {
        delays[i].style.display = "none";
        delays[i].style.visibility = "hidden";
    }
    var divs = document.getElementsByClassName(toShow)
    for(i = 0; i < divs.length; ++i)
    {
        divs[i].style.display="block";
        divs[i].style.visibility="visible";
    }
}
