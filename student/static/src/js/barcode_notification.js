/** archivo static/src/js/barcode_notification.js **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class LibraryAccessNotification {
    setup() {
        this.notification = useService("notification");
        
        onMounted(() => {
            this.el.querySelector("input[name='barcode']").addEventListener("change", async (event) => {
                const barcode = event.target.value;
                if (barcode) {
                    // Mostrar notificación de registro de ingreso
                    this.notification.add(`Ingreso registrado para el código de barras: ${barcode}`, {
                        type: "success",
                        duration: 2000,
                    });
                }
            });
        });
    }
}

registry.category("actions").add("LibraryAccessNotification", LibraryAccessNotification);
