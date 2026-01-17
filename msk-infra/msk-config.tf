resource "aws_msk_configuration" "video_config" {
  name           = "video-batch-config"
  kafka_versions = ["3.6.0"]

  server_properties = <<EOF
auto.create.topics.enable=true
message.max.bytes=10485760
replica.fetch.max.bytes=10485760
socket.request.max.bytes=10485760
EOF
}

