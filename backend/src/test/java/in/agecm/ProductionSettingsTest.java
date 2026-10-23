package in.agecm;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import static org.junit.jupiter.api.Assertions.*;
class ProductionSettingsTest {
 @TempDir Path folder;
 ProductionSettings configured()throws Exception{ProductionSettings p=new ProductionSettings();p.mode="LIVE";p.token="a-private-token-with-more-than-32-characters";p.password="private-password-long-enough";p.origins="https://monitor.example.org";p.caPath=folder.resolve("ca.pem").toString();Files.writeString(Path.of(p.caPath),"unit fixture only");p.database="jdbc:postgresql://private.example.org:5432/agecm?sslmode=verify-full&sslrootcert="+p.caPath;return p;}
 @Test void requiresPrivateSecretsAndLiveMode()throws Exception{ProductionSettings p=configured();assertDoesNotThrow(p::validate);p.token="local-development-token";assertThrows(IllegalStateException.class,p::validate);p=configured();p.mode="DEMO";assertThrows(IllegalStateException.class,p::validate);}
 @Test void requiresVerifiedTlsAndHttpsOrigin()throws Exception{ProductionSettings p=configured();p.database=p.database.replace("verify-full","require");assertThrows(IllegalStateException.class,p::validate);p=configured();p.origins="http://localhost:5173";assertThrows(IllegalStateException.class,p::validate);p=configured();Files.delete(Path.of(p.caPath));assertThrows(IllegalStateException.class,p::validate);}
}
