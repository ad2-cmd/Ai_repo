<?php
 
function my_theme_enqueue_styles() {
 
    $parent_style = 'parent-style'; // This is 'twentytwentytwo-style' for the Twenty seventeen theme.
 
    wp_enqueue_style( $parent_style, get_template_directory_uri() . '/style.css' );
    wp_enqueue_style( 'child-style',
        get_stylesheet_directory_uri() . '/style.css',
        array( $parent_style ),
        wp_get_theme()->get('Version')
    );
}
add_action( 'wp_enqueue_scripts', 'my_theme_enqueue_styles' );

add_action('admin_head', 'admin_styles');
function admin_styles() {
     echo '<style>
            .wp-block {max-width: 1720px;}
            .wp-block[data-align="wide"] {max-width: 2280px;}
            </style>';
}
 

