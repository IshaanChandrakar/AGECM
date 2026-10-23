package in.agecm;
import jakarta.annotation.PostConstruct;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;
import java.nio.file.*;
@Component @Profile("production")
public class ProductionSettings {
 @Value("${agecm.mode}") String mode;
 @Value("${agecm.ingestion-token}") String token;
 @Value("${spring.datasource.password}") String password;
 @Value("${spring.datasource.url}") String database;
 @Value("${agecm.origins}") String origins;
 @Value("${agecm.db-ca-path:/app/certs/global-bundle.pem}") String caPath;
 @Value("${agecm.fixture:false}") boolean fixture;
 @PostConstruct void validate(){
  if(!"LIVE".equals(mode)||fixture)fail();
  if(token==null||token.length()<32||token.contains("REPLACE")||token.equals("local-development-token"))fail();
  if(password==null||password.length()<16||password.contains("REPLACE")||password.equals("agecm_local"))fail();
  if(database==null||!database.startsWith("jdbc:postgresql://")||!database.contains("sslmode=verify-full")||!database.contains("sslrootcert="+caPath)||!Files.isReadable(Path.of(caPath)))fail();
  for(String origin:origins.split(","))if(!origin.matches("https://[A-Za-z0-9.-]+(?::[0-9]+)?")||origin.contains("localhost")||origin.contains("127.0.0.1"))fail();
 }
 void fail(){throw new IllegalStateException("Production requires LIVE mode, private non-default secrets, HTTPS origins and verified PostgreSQL TLS with the mounted CA bundle");}
}
