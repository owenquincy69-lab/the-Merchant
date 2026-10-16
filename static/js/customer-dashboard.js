
"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const copyButton = document.getElementById("copyReferralLink");
    const linkText = document.getElementById("referralLinkText");
    const status = document.getElementById("referralCopyStatus");

    copyButton?.addEventListener("click", async () => {
        const value = linkText?.textContent?.trim() || "";

        if (!value || value.includes("not available yet")) {
            if (status) {
                status.textContent = "Your referral link is not available yet.";
            }
            return;
        }

        try {
            await navigator.clipboard.writeText(value);

            if (status) {
                status.textContent = "Referral link copied.";
            }
        } catch (error) {
            if (status) {
                status.textContent =
                    "Copying was blocked by your browser. Select the link and copy it manually.";
            }
        }
    });
});
