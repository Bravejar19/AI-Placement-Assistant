import os
import base64


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".txt",
    ".rtf"
}


def get_attachments(payload):
    attachments = []

    def scan_parts(parts):
        for part in parts:

            filename = part.get("filename", "")
            body = part.get("body", {})

            if filename:

                extension = os.path.splitext(
                    filename
                )[1].lower()

                if extension in ALLOWED_EXTENSIONS:

                    attachments.append({
                        "filename": filename,
                        "mime_type": part.get("mimeType"),
                        "attachment_id": body.get("attachmentId"),
                        "size": body.get("size", 0)
                    })

            if "parts" in part:
                scan_parts(part["parts"])

    if "parts" in payload:
        scan_parts(payload["parts"])

    return attachments


def download_attachment(
        service,
        message_id,
        attachment_id,
        filename,
        output_directory
):

    attachment = service.users().messages().attachments().get(
        userId="me",
        messageId=message_id,
        id=attachment_id
    ).execute()

    data = attachment.get("data")

    if not data:
        return None

    file_data = base64.urlsafe_b64decode(
        data
    )

    os.makedirs(
        output_directory,
        exist_ok=True
    )

    file_path = os.path.join(
        output_directory,
        filename
    )

    with open(file_path, "wb") as file:
        file.write(file_data)

    return file_path