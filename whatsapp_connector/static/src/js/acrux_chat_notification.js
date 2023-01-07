/** @odoo-module **/

import { registry } from "@web/core/registry";


var notifactions_hash = new Map()
var legacyEnv = {}
var actionService = {}

/**
 * Indica si la pestaña es una pestaña de chatroom
 * @returns {Boolean}
 */
function isChatroomTab() {
    let out = false
    const currentController = actionService.currentController
    if (currentController) {
        if (currentController.action.tag) {
            out = currentController.action.tag === "acrux.chat.conversation_tag"
        } else {
            out = !!currentController.acrux_comp 
        }
    }
   return out
}
    
 export const processNotification = {
    /**
     * Muestra la notificacion en el navegador
     * @param {Array<Array<Object>>} data
     */
     process: function(data) {
        let msg = null

        data.forEach(row => {
            msg = row.find(conv => conv.desk_notify == 'all')
            if (!msg) {
                msg = row.find(conv =>
                    conv.desk_notify == 'mines'&&
                    conv.agent_id &&
                    conv.agent_id[0] == legacyEnv.session.uid)
            }
        })
        if (msg) {
            if (msg.messages && msg.messages.length && msg.messages[0].ttype == 'text') {
                legacyEnv.services.bus_service.sendNotification({
                    title: legacyEnv._t('New Message from ') + msg.name,
                    message: msg.messages[0].text  
                })
            } else {
                legacyEnv.services.bus_service.sendNotification({
                    title: legacyEnv._t('New Message from ') + msg.name,
                    message: ''  
                })
            }
        }
    }
}

/**
 * Procesa las notificaciones que vienen del bus
 * @param {Array<Object>} notifications
 */
function onNotifaction(notifications) {
    if (Notification && Notification.permission === "granted") {
        /** @type {Array} */
        var data = notifications
            .filter(item => item.type === 'new_messages')
            .map(item => item.payload)  // se filtran las notificaciones de chatroom
        if (data && data.length) {
            let json = JSON.stringify(data)
            if (isChatroomTab()) {
                /** 
                    Si hay una pestaña de chatroom abierta entonces
                    se notifica a las demas pestañas que no deben mostrar la 
                    notificacion 
                */
                legacyEnv.services.local_storage.setItem('chatroom_notification', json);
            } else {
                /**
                    Se almacena en un Map, el json de la notificacion y un timeout
                    para mostrar esta notificaciones.
                    Si el timeout no se cancela entonces muestra la notifiacion.
                 */
                notifactions_hash.set(json, setTimeout(() => {
                    processNotification.process(data)
                    notifactions_hash.delete(json);
                }, 50)) /** @bug posible bug con el timeout */ 
            }
        }
    }
}

/**
 * Procesa el evento de almacenar.
 * Este evento se lanza cuando se recibe una notificion y se esta en la pestaña
 * de chatroom, basicamente es para evitar que se muestre la notificacion
 *
 * @param {OdooEvent} event
 * @param {string} event.key
 * @param {string} event.newValue
 */
function onStorage(event) {
    if (event.key === 'chatroom_notification') {
        const value = JSON.parse(event.newValue)
        if (notifactions_hash.has(value)) {  // si la notificacion esta esperando para mostrarse
            clearTimeout(notifactions_hash.get(value))  // no mostra notificaion
            notifactions_hash.delete(value)
        }
    }
}

export const chatroomNotificationService = {
    dependencies: ['action'],

    start(env, {action}) {
        legacyEnv = owl.Component.env
        actionService = action
        env.bus.on("WEB_CLIENT_READY", null, async () => {
            legacyEnv.services.bus_service.onNotification(this, onNotifaction);
            /** @bug en web/legacy/utils.js */
            $(window).on('storage', e => {
                var key = e.originalEvent.key;
                var newValue = e.originalEvent.newValue;
                try {
                    JSON.parse(newValue);
                    onStorage({
                        key: key,
                        newValue: newValue,
                    })
                } catch (error) {}
            });
            legacyEnv.services.bus_service.startPolling();
        });

    },
}

registry.category("services").add("chatroomNotification", chatroomNotificationService)
