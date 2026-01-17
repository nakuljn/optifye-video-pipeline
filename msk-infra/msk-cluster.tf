resource "aws_msk_cluster" "video_msk" {
  cluster_name           = "video-pipeline"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    client_subnets  = [
       data.aws_subnet.az1.id,
       data.aws_subnet.az2.id,
       data.aws_subnet.az3.id
    ]
    security_groups = [aws_security_group.msk_sg.id]

    storage_info {
      ebs_storage_info {
        volume_size = 10
      }
    }
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.video_config.arn
    revision = aws_msk_configuration.video_config.latest_revision
  }
}

