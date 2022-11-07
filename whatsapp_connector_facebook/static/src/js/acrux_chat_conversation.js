odoo.define('whatsapp_connector_facebook.conversation', function(require) {
"use strict";

var Conversation = require('whatsapp_connector.conversation');

/**
 * @class
 * @name Conversation
 * @extends whatsapp.Conversation
 */
Conversation.include({
    /**
     * Devuelve si el conector pertenece a facebook
     * @returns {Boolean}
     */
    isOwnerFacebook: function() {
        return ['facebook', 'instagram'].includes(this.connector_type)
    },

    /**
     * Retorna la clase para mostrar el icono
     */
    getIconClass: function() {
        let out = ''
        if (this.connector_type === 'facebook') {
            out = 'acrux_messenger'
        } else if (this.connector_type === 'instagram') {
            out = 'acrux_instagram'
        } else {
            out = this._super()
        }
        return out
    }

})

return Conversation
})
