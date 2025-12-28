<?php
/**
 * Theme functions for Zero Obstacle
 */

// Enqueue parent and child styles
function zero_obstacle_enqueue_styles() {
    wp_enqueue_style('parent-style', get_template_directory_uri() . '/style.css');
    wp_enqueue_style('child-style', get_stylesheet_uri(), array('parent-style'));
}
add_action('wp_enqueue_scripts', 'zero_obstacle_enqueue_styles');

// Register translations
function zero_obstacle_load_textdomain() {
    load_child_theme_textdomain('zero-obstacle', get_stylesheet_directory() . '/languages');
}
add_action('after_setup_theme', 'zero_obstacle_load_textdomain');

// Register custom page templates
function zero_obstacle_register_templates($templates) {
    $templates['page-templates/tpl-home.php'] = __('Accueil / Home', 'zero-obstacle');
    $templates['page-templates/tpl-transparency.php'] = __('Transparence / Transparency', 'zero-obstacle');
    $templates['page-templates/tpl-tools.php'] = __('Outils / Tools', 'zero-obstacle');
    $templates['page-templates/tpl-testimonials.php'] = __('Témoignages / Testimonials', 'zero-obstacle');
    return $templates;
}
add_filter('theme_page_templates', 'zero_obstacle_register_templates');

// Shortcode impact table
function zero_obstacle_impact_table_shortcode() {
    ob_start();
    ?>
    <table class="impact-table">
        <thead>
            <tr>
                <th><?php _e('Profil utilisateur', 'zero-obstacle'); ?></th>
                <th><?php _e('Ce que l\'outil permet', 'zero-obstacle'); ?></th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><?php _e('Retraite isolée', 'zero-obstacle'); ?></td>
                <td><?php _e('Identifie les aides non réclamées et imprime les formulaires requis', 'zero-obstacle'); ?></td>
            </tr>
            <tr>
                <td><?php _e('Étudiant en difficulté', 'zero-obstacle'); ?></td>
                <td><?php _e('Accède à des subventions et à l\'aide juridique en cas de litige', 'zero-obstacle'); ?></td>
            </tr>
            <tr>
                <td><?php _e('Parent d\'enfant handicapé', 'zero-obstacle'); ?></td>
                <td><?php _e('Reçoit les crédits d\'impôt et les services spécialisés disponibles', 'zero-obstacle'); ?></td>
            </tr>
            <tr>
                <td><?php _e('Immigrant nouvel arrivant', 'zero-obstacle'); ?></td>
                <td><?php _e('Comprend ses droits et accède aux prestations en plusieurs langues', 'zero-obstacle'); ?></td>
            </tr>
            <tr>
                <td><?php _e('Travailleur précaire', 'zero-obstacle'); ?></td>
                <td><?php _e('Conteste les frais bancaires et obtient un soutien budgétaire', 'zero-obstacle'); ?></td>
            </tr>
        </tbody>
    </table>
    <?php
    return ob_get_clean();
}
add_shortcode('impact_table', 'zero_obstacle_impact_table_shortcode');
?>
