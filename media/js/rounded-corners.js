/*
written by Pachollini (Matej Novak) http://seky.nahory.net/
original najdete na http://seky.nahory.net/2005/04/kulate-rohy-nifty-corners/
see http://seky.nahory.net/2005/04/rounded-corners/ for description
inspired by Alessandro Fulciniti's http://pro.html.it/esempio/nifty/

version 1.2: Safari bug fixed
version 1.1: limited support for rounded borders added

this script is free to use, modify, sell and whatever you might want to do with it
keeping notice about the author or linking my website is highly appreciated
enjoy :-)

*/

function make_corners()
	{
	var $i;
	var $elements=find_class(document.body,"rounded");
	if(!(navigator.appName=="Microsoft Internet Explorer" && navigator.appVersion.indexOf("5.5")>-1)) for($i in $elements) rounded_corners($elements[$i]);
	}

function rounded_corners($element)
	{
	var $rc_radius=10, $rc_left=true, $rc_right=true, $rc_top=true, $rc_bottom=true, $rc_self_color, $rc_parent_color, $rc_antialiased,$rc_antialiased_cf=0.33,$rc_compact,$rc_auto_margin,$rc_method="margin",$rc_border,$border_color;
	var	$property,$container,$el_container,$el_inner,$j,$i,$ang,$ang_last,$bw,$width,ee,$err_alert;
	var $classes=$element.className.split(" ");
	$rc_self_color=get_current_style($element,"background-color","(transparent)|(rgba)");
	$rc_parent_color=get_current_style($element.parentNode,"background-color","(transparent)|(rgba)");
	$border_color=get_current_style($element,"border-top-color");
	for ($i in $classes)
		{
		$property=$classes[$i].split("-");
		if($property[0]=="rc") switch ($property[1])
			{
			case "radius":
				$rc_radius=$property[2];
				break;
			case "top":
				$rc_top=$property[2]!="0"?true:false;
				break;
			case "left":
				$rc_left=$property[2]!="0"?true:false;
				break;
			case "right":
				$rc_right=$property[2]!="0"?true:false;
				break;
			case "bottom":
				$rc_bottom=$property[2]!="0"?true:false;
				break;
			case "selfcolor":
				$rc_self_color="#"+$property[2];
				break;
			case "parentcolor":
				$rc_parent_color=$property[2]=="transparent"?"transparent":"#"+$property[2];
				break;
			case "inheritstylecolors":
				$rc_parent_color=$property[2]!="0"?false:true;
				$rc_self_color=$property[2]!="0"?false:true;
				break;
			case "antialiased":
				$rc_antialiased=$property[2]!="0"?true:false;
				break;
			case "antialiasedcf":
				$rc_antialiased_cf=parseFloat($property[2]);
				break;
			case "compact":
				$rc_compact=$property[2]!="0"?true:false;
				break;
			case "automargin":
				$rc_auto_margin=$property[2]!="0"?true:false;
				break;
			case "method":
				$rc_method=$property[2];
				break;
			case "border":
				$rc_method="margin";
				$rc_border=true;
				$element.style.border="none";
				break;
			}
		}
	if($rc_antialiased && $rc_method=="margin")
		{
		var $arr_self_color=color2array($rc_self_color);
		var $arr_parent_color=$rc_border?color2array($border_color):color2array($rc_parent_color);
		if($arr_self_color!=false && $arr_parent_color!=false) var $rc_antialiased_color="rgb("+Math.round(($arr_parent_color[0]-$arr_self_color[0])*$rc_antialiased_cf+$arr_self_color[0])+","+Math.round(($arr_parent_color[1]-$arr_self_color[1])*$rc_antialiased_cf+$arr_self_color[1])+","+Math.round(($arr_parent_color[2]-$arr_self_color[2])*$rc_antialiased_cf+$arr_self_color[2])+")";
		else $rc_antialiased=false;
		}
	var $containers=new Array();
	if($rc_top)$containers[0]="top";
	if($rc_bottom)$containers[$containers.length]="bottom";
	if(!$rc_parent_color)$rc_parent_color=get_current_style(document.body,"background-color");
	for($j in $containers)
		{
		$container=$containers[$j];
		$el_container=document.createElement("div");
		$el_container.className="rc-container-"+$container;
		if($rc_parent_color && $rc_method=="margin")
		    {
		    try
		      {
		      $el_container.style.backgroundColor=$rc_parent_color;
		      }
		     catch(ee){self.status="Chyba nastaveni pozadi."}
		    }
		$el_container.style.height=$rc_radius+"px";
		for($i=0;$i<$rc_radius;$i++)
			{
			$el_inner=document.createElement("span");
			if($rc_self_color && $rc_method=="margin")$el_inner.style.backgroundColor=$rc_self_color;
			$el_inner.style.display="block";
			$el_inner.className="rc-inner rc-level-"+$i;
			$ang=Math.asin($i/$rc_radius);
			$el_inner.style.height="1px";
			$el_inner.style.overflow="hidden";
			$width=($rc_radius-Math.round($rc_radius*Math.cos($ang)));
			if($rc_method=="margin")
				{
				$el_inner.style.margin="0 "+($rc_right?$width:"0")+"px 0 "+($rc_left?$width:"0")+"px";
				if($rc_antialiased || $rc_border)
					{
					$bw=Math.ceil($rc_radius*Math.cos(Math.asin(($i-1)/$rc_radius))-$rc_radius*Math.cos($ang));
					if($bw==0)$bw=1;
					$el_inner.style.borderWidth="0 "+($rc_right?$bw:"0")+"px 0 "+($rc_left?$bw:"0")+"px";
					if(!$rc_border)
						{
						try{$el_inner.style.borderColor=$rc_antialiased_color;}
						catch($ee){if(!$err_alert)alert("There's probably a wrong CSS declaration of color used (use '#000000' instead of 'black' or '#000'.");$err_alert=true;}
						}
					else
						{
						$el_inner.style.borderColor=($rc_antialiased && $width) ? $rc_antialiased_color : $border_color;
						if($i==$rc_radius-1)
							{
							$el_inner.style.backgroundColor=$border_color;
							}
						}
					$el_inner.style.borderStyle="solid";
					}
				}
			else
				{
				if($rc_parent_color)$el_inner.style.borderColor=$rc_parent_color;
				$el_inner.style.borderStyle="solid";
				$el_inner.style.borderWidth="0 "+($rc_right?$width:"0")+"px 0 "+($rc_left?$width:"0")+"px";
				}
			if($container=="top" && $el_container.firstChild)$el_container.insertBefore($el_inner.cloneNode(true),$el_container.firstChild);
			else $el_container.appendChild($el_inner.cloneNode(true));
			delete $el_inner;
			}
		if($rc_compact)
			{
			if($container=="top") $el_container.style.marginBottom="-"+$rc_radius+"px";
			else $el_container.style.marginTop="-"+$rc_radius+"px";
			}
		if($rc_auto_margin)
			{
			$el_container.style.marginLeft="-"+get_current_style($element,"padding-left");
			$el_container.style.marginRight="-"+get_current_style($element,"padding-right");
			if($container=="top") $el_container.style.marginTop="-"+get_current_style($element,"padding-top");
			else $el_container.style.marginBottom="-"+get_current_style($element,"padding-bottom");
			}
		if($container=="top" && $element.firstChild)$element.insertBefore($el_container.cloneNode(true),$element.firstChild);
		else $element.appendChild($el_container.cloneNode(true));
		delete $container;
		}
	}

// common functions:

function find_class($element,$classnames,$result,$first)
  {
  if(!$first)$first=$element;
  if(!$result)$result=new Array();
  if ($element.nodeType==1)
    {
    var $test_exp=new RegExp("(^| )("+$classnames+")( |$)");
    if($test_exp.test($element.className)) $result[$result.length]=$element;
    }
  if ($element.hasChildNodes()) $result=find_class($element.firstChild,$classnames,$result,$first);
  if ($element.nextSibling && $element!=$first) $result=find_class($element.nextSibling,$classnames,$result,$first);
  return $result;
  }

function get_current_style($element,$property,$not_accepted)
  {
  var ee,$i,$val,$apr;
  var $na=new RegExp($not_accepted);
  try
    {
    var $cs=document.defaultView.getComputedStyle($element,'');
    $val=$cs.getPropertyValue($property);
    }
  catch(ee)
    {
    if($element.currentStyle)
    	{
	    $apr=$property.split("-");
	    for($i=1;$i<$apr.length;$i++) $apr[$i]=$apr[$i].toUpperCase();
	    $apr=$apr.join("");
	    $val=$element.currentStyle.getAttribute($apr);
	    }
    }
  
  if($not_accepted && $na.test($val) && $element.parentNode) $val=get_current_style($element.parentNode,$property,$not_accepted);
  return $val;
  }

function color2array($value)
	{
	if($value.substr(0,1)=="#")return hex2array($value);
	else if($value.indexOf("rgb")>-1) return rgb2array($value);
	else return false;
	}

function rgb2array($value)
	{
	var $i;
	var $regexp=/([0-9]+)[, ]+([0-9]+)[, ]+([0-9]+)/;
	var $array=$regexp.exec($value);
	$array.shift();
	for($i=0;$i<3;$i++)$array[$i]=parseInt($array[$i]);
	return($array);
	}

function hex2array($value)
	{
	return new Array(parseInt($value.substr(1,2),16),parseInt($value.substr(3,2),16),parseInt($value.substr(5,2),16));
	}