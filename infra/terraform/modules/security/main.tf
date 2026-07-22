resource "aws_kms_key" "platform" {
  description             = "${var.name_prefix} application data encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_kms_alias" "platform" {
  name          = "alias/${var.name_prefix}-platform"
  target_key_id = aws_kms_key.platform.key_id
}
