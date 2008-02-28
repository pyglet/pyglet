<?php
$BASE_URL = 'http://groups.google.com';
$FEED_URL = 
  'http://groups.google.com/group/pyglet-users/feed/atom_v1_0_msgs.xml';
$MAX_DISCUSSION_ENTRIES = 3;

function get_pages()
{
  global $BASE_URL;

  echo "Reading $BASE_URL/group/pyglet-users/web/...<br/>\n";

  $pages = array();
  $html = file_get_contents($BASE_URL . '/group/pyglet-users/web/');
  preg_match_all('|class="name ln"  href="([^"]*)">([^<]*)</a>|s', $html,
                 $matches, PREG_SET_ORDER);
  foreach ($matches as $match)
  {
    $url = $BASE_URL . $match[1];
    $name = trim($match[2]);
    echo "Reading $url...<br/>\n";
    $image = get_page_image($url);
    if ($image)
    {
      $pages[] = array($name, $url, $image);
    }
  }
  return $pages;
}

function get_page_image($url)
{
  global $BASE_URL;

  $html = file_get_contents($url);
  $count = preg_match('|<img src="(http://groups.google.com)?(/group/pyglet-users/web/[^?"]*)|', $html,
                      $matches);
  if ($count)
  {
    return $BASE_URL . $matches[2];
  }

  return NULL;
}

function update_gallery()
{
  $pages = get_pages();
  echo "Result:<p>\n";
  echo "<pre>\n";
  $gallery_fp = fopen('gallery-items.txt', 'w');
  echo $gallery_fp . "\n";
  foreach ($pages as $page)
  {
    list($name, $url, $image) = $page;
    fwrite($gallery_fp, $name . "\n");
    fwrite($gallery_fp, $url . "\n");
    fwrite($gallery_fp, $image . "\n");
    echo "$name\n$url\n$image\n";
  }
  fclose($gallery_fp);
  echo "</pre>\n";
  echo "done.<br/>\n";
}

function update_discussion()
{
  global $FEED_URL;
  global $MAX_DISCUSSION_ENTRIES;

  echo "Downloading feed...<br>\n";
  $feed = file_get_contents($FEED_URL);
  $doc = domxml_open_mem($feed);
  $entry_count = 0;
  $doc_element = $doc->document_element();
  $child_nodes = $doc_element->child_nodes();
  foreach ($child_nodes as $node)
  {
    if ($node->node_type() == XML_ELEMENT_NODE && 
        $node->node_name() == 'entry')
    {
      $entry_count += 1;
      if ($entry_count > $MAX_DISCUSSION_ENTRIES)
      {
        $doc_element->remove_child($node);
      }
    }
  }
  $doc->dump_file('pyglet-users.xml');
}

ob_end_flush();
update_gallery();
//update_discussion();
?>
