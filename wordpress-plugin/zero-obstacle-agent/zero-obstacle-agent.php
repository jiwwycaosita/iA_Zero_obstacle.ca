<?php
/**
 * Plugin Name: Zero Obstacle Agent
 * Description: Connecte WordPress à ton orchestrateur d'agents Zero Obstacle (FastAPI sur ton PC).
 * Version: 0.1.0
 * Author: Zero Obstacle IA
 */

if (!defined('ABSPATH')) {
    exit;
}

// Option pour stocker l'URL de l'API (ex: http://192.168.0.10:8080)
function zoa_register_settings() {
    add_option('zoa_api_url', 'http://localhost:8080');
    register_setting('zoa_options_group', 'zoa_api_url', 'esc_url_raw');
}
add_action('admin_init', 'zoa_register_settings');

function zoa_register_options_page() {
    add_options_page('Zero Obstacle Agent', 'Zero Obstacle Agent', 'manage_options', 'zoa', 'zoa_options_page');
}
add_action('admin_menu', 'zoa_register_options_page');

function zoa_options_page() {
    ?>
    <div class="wrap">
        <h1>Zero Obstacle Agent</h1>
        <form method="post" action="options.php">
            <?php settings_fields('zoa_options_group'); ?>
            <table class="form-table">
                <tr valign="top">
                    <th scope="row">URL de l'API FastAPI</th>
                    <td>
                        <input type="text" name="zoa_api_url" style="width: 400px;"
                               value="<?php echo esc_attr(get_option('zoa_api_url')); ?>" />
                        <p class="description">Ex: http://TON_PC:8080</p>
                    </td>
                </tr>
            </table>
            <?php submit_button(); ?>
        </form>
    </div>
    <?php
}

// Shortcode [zero_obstacle_form]
function zoa_form_shortcode() {
    $api_url = esc_url(get_option('zoa_api_url'));

    $output = '';

    if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['zoa_question']) && check_admin_referer('zoa_form_action', 'zoa_form_nonce')) {
        $question = sanitize_textarea_field($_POST['zoa_question']);

        $body = wp_json_encode(array(
            'task' => 'general',
            'text' => $question,
        ));

        $response = wp_remote_post(rtrim($api_url, '/') . '/agent/orchestrate', array(
            'headers' => array('Content-Type' => 'application/json'),
            'body'    => $body,
            'timeout' => 60,
        ));

        if (is_wp_error($response)) {
            $output .= '<div style="color:red;">Erreur de connexion à l’agent : ' . esc_html($response->get_error_message()) . '</div>';
        } else {
            $status_code = wp_remote_retrieve_response_code($response);
            $response_body = wp_remote_retrieve_body($response);
            if ($status_code === 200) {
                $data = json_decode($response_body, true);
                $answer = isset($data['result']['answer']) ? esc_html($data['result']['answer']) : 'Aucune réponse.';
                $output .= '<h3>Réponse de l’agent :</h3><pre style="white-space:pre-wrap;">' . $answer . '</pre>';
            } else {
                $output .= '<div style="color:red;">Erreur API (' . intval($status_code) . ') : ' . esc_html($response_body) . '</div>';
            }
        }
    }

    ob_start();
    ?>
    <form method="post">
        <?php wp_nonce_field('zoa_form_action', 'zoa_form_nonce'); ?>
        <p>
            <label for="zoa_question">Votre question pour Zéro Obstacle :</label><br>
            <textarea id="zoa_question" name="zoa_question" rows="5" cols="60" required></textarea>
        </p>
        <p>
            <button type="submit">Envoyer à l’agent</button>
        </p>
    </form>
    <?php
    $form_html = ob_get_clean();

    return $output . $form_html;
}
add_shortcode('zero_obstacle_form', 'zoa_form_shortcode');
